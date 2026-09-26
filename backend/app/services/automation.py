"""Enterprise Automation Service for SAP PM and QMS Workflows.

Features:
- Policy evaluator supporting site scoping and risk thresholds
- Dry-run simulation mode (simulates payload & impact without DB mutations)
- Human-in-the-loop approval routing for high-impact actions
- Deterministic rollback and compensation guidance for target systems
- Comprehensive audit event logging
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session

from backend.app.db.models import ApprovalRecord, AuditEvent, AutomationPolicy

logger = logging.getLogger(__name__)

DEFAULT_POLICIES = [
    {
        "policy_id": "POL-SAP-PM-CRITICAL",
        "site_id": "*",
        "name": "Auto-Draft SAP Work Order on Critical Health Index",
        "description": "Automatically stages a draft SAP PM maintenance work order (priority 1) when equipment health index drops below 40.",
        "trigger_type": "HEALTH_INDEX_CRITICAL",
        "action_type": "CREATE_SAP_WORK_ORDER",
        "target_system": "SAP_PM",
        "approval_threshold": "REQUIRES_APPROVAL",
        "parameters": {"threshold": 40, "order_type": "PM02", "priority": "1"},
        "rollback_guidance": "SAP PM Rollback: Run transaction IW32 in SAP GUI; set order status to TECO/CLSD or delete draft. Or call DELETE /api/work-orders/{order_id}.",
    },
    {
        "policy_id": "POL-QMS-STATUTORY",
        "site_id": "*",
        "name": "Auto-Log QMS CAPA on Statutory Inspection Overdue",
        "description": "Creates a Corrective & Preventive Action (CAPA) finding in QMS when statutory inspection window is exceeded.",
        "trigger_type": "STATUTORY_OVERDUE",
        "action_type": "LOG_QMS_CAPA",
        "target_system": "QMS",
        "approval_threshold": "REQUIRES_APPROVAL",
        "parameters": {"severity": "MAJOR", "due_days": 14},
        "rollback_guidance": "QMS Rollback: Open QMS Quality Portal, locate CAPA reference, and update disposition to 'VOID - DUPLICATE / RETRACTED' with engineering signoff.",
    },
    {
        "policy_id": "POL-PI-VIBRATION",
        "site_id": "*",
        "name": "Autonomous Work Order Draft for ISO 10816 Vibration Spike",
        "description": "Stages an urgent vibration diagnostic work order when vibration exceeds ISO 10816 threshold (> 4.5 mm/s).",
        "trigger_type": "VIBRATION_SPIKE",
        "action_type": "CREATE_SAP_WORK_ORDER",
        "target_system": "SAP_PM",
        "approval_threshold": "AUTONOMOUS",
        "parameters": {"vibration_threshold_mms": 4.5, "order_type": "PM01", "priority": "2"},
        "rollback_guidance": "SAP PM Rollback: Cancel maintenance order via transaction IW38 or archive work order record.",
    },
]


def seed_default_policies_if_empty(db: Session) -> None:
    """Ensure baseline industrial automation policies are populated."""
    count = db.query(AutomationPolicy).count()
    if count == 0:
        for p in DEFAULT_POLICIES:
            policy = AutomationPolicy(
                policy_id=p["policy_id"],
                site_id=p["site_id"],
                name=p["name"],
                description=p["description"],
                trigger_type=p["trigger_type"],
                action_type=p["action_type"],
                target_system=p["target_system"],
                approval_threshold=p["approval_threshold"],
                parameters_json=json.dumps(p["parameters"]),
                rollback_guidance=p["rollback_guidance"],
                is_active=True,
            )
            db.add(policy)
        db.commit()


def list_automation_policies(db: Session, site_id: str | None = None) -> list[dict[str, Any]]:
    """List automation policies for a site or global."""
    seed_default_policies_if_empty(db)
    query = db.query(AutomationPolicy)
    if site_id:
        query = query.filter((AutomationPolicy.site_id == site_id) | (AutomationPolicy.site_id == "*"))
    policies = query.order_by(AutomationPolicy.created_at.desc()).all()
    return [p.to_dict() for p in policies]


def create_or_update_policy(db: Session, policy_data: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Create or update an automation policy."""
    policy_id = policy_data.get("policy_id") or f"POL-{uuid.uuid4().hex[:8].upper()}"
    policy = db.query(AutomationPolicy).filter(AutomationPolicy.policy_id == policy_id).first()

    params = policy_data.get("parameters", {})
    params_json = json.dumps(params) if isinstance(params, dict) else str(params)

    if not policy:
        policy = AutomationPolicy(
            policy_id=policy_id,
            site_id=policy_data.get("site_id", "*"),
            name=policy_data["name"],
            description=policy_data.get("description"),
            trigger_type=policy_data["trigger_type"],
            action_type=policy_data["action_type"],
            target_system=policy_data["target_system"],
            approval_threshold=policy_data.get("approval_threshold", "REQUIRES_APPROVAL"),
            parameters_json=params_json,
            rollback_guidance=policy_data.get("rollback_guidance"),
            is_active=policy_data.get("is_active", True),
        )
        db.add(policy)
        action_name = "AUTOMATION_POLICY_CREATED"
    else:
        policy.name = policy_data.get("name", policy.name)
        policy.description = policy_data.get("description", policy.description)
        policy.trigger_type = policy_data.get("trigger_type", policy.trigger_type)
        policy.action_type = policy_data.get("action_type", policy.action_type)
        policy.target_system = policy_data.get("target_system", policy.target_system)
        policy.approval_threshold = policy_data.get("approval_threshold", policy.approval_threshold)
        policy.parameters_json = params_json
        policy.rollback_guidance = policy_data.get("rollback_guidance", policy.rollback_guidance)
        policy.is_active = policy_data.get("is_active", policy.is_active)
        action_name = "AUTOMATION_POLICY_UPDATED"

    # Audit event
    audit = AuditEvent(
        user_id=user_id,
        site_id=policy.site_id,
        role="AutomationAdmin",
        action_type=action_name,
        resource_type="automation_policy",
        resource_id=policy.policy_id,
        details_json=json.dumps({"name": policy.name, "trigger": policy.trigger_type}),
        status="SUCCESS",
    )
    db.add(audit)
    db.commit()
    db.refresh(policy)
    return policy.to_dict()


def evaluate_automation_trigger(
    db: Session,
    trigger_type: str,
    site_id: str,
    context_data: dict[str, Any],
    user_id: str = "system",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Evaluate active policies against incoming telemetry or compliance events.
    Supports dry_run simulation without mutating the database.
    """
    seed_default_policies_if_empty(db)
    policies = (
        db.query(AutomationPolicy)
        .filter(
            (AutomationPolicy.site_id == site_id) | (AutomationPolicy.site_id == "*"),
            AutomationPolicy.trigger_type == trigger_type,
            AutomationPolicy.is_active == True,
        )
        .all()
    )

    triggered_actions = []

    for policy in policies:
        params = json.loads(policy.parameters_json) if policy.parameters_json else {}
        should_trigger = False
        reason = ""

        if trigger_type == "HEALTH_INDEX_CRITICAL":
            threshold = params.get("threshold", 40)
            health = context_data.get("health_index", 100)
            if health < threshold:
                should_trigger = True
                reason = f"Health index ({health}) breached critical threshold ({threshold})"

        elif trigger_type == "STATUTORY_OVERDUE":
            status = context_data.get("status") or context_data.get("audit_status")
            if status in ("OVERDUE", "AUDIT_FAILED_GAPS_FOUND"):
                should_trigger = True
                reason = f"Statutory inspection non-compliance detected: {context_data.get('clause_id', 'General Statutory Audit')}"

        elif trigger_type == "VIBRATION_SPIKE":
            thresh = params.get("vibration_threshold_mms", 4.5)
            vib = context_data.get("vibration_mms", 0.0)
            if vib >= thresh:
                should_trigger = True
                reason = f"Vibration ({vib} mm/s) exceeded ISO 10816 threshold ({thresh} mm/s)"

        else:
            # Generic trigger fallback
            should_trigger = True
            reason = f"Event trigger {trigger_type} satisfied"

        if should_trigger:
            equipment_tag = context_data.get("equipment_tag", "UNKNOWN")
            
            # Construct target payload
            if policy.action_type == "CREATE_SAP_WORK_ORDER":
                payload = {
                    "equipment_tag": equipment_tag,
                    "order_type": params.get("order_type", "PM02"),
                    "priority": params.get("priority", "1"),
                    "title": f"Work Order for {equipment_tag} - {reason}",
                    "description": f"Automated trigger by policy {policy.policy_id} ({policy.name}). Details: {reason}",
                    "site_id": site_id,
                    "recommended_action": context_data.get("recommended_turnaround", "Immediate inspection"),
                }
            elif policy.action_type == "LOG_QMS_CAPA":
                payload = {
                    "equipment_tag": equipment_tag,
                    "clause_id": context_data.get("clause_id", "STATUTORY-GAP"),
                    "severity": params.get("severity", "MAJOR"),
                    "issue_summary": f"Statutory audit overdue for {equipment_tag}: {reason}",
                    "target_due_days": params.get("due_days", 14),
                    "site_id": site_id,
                }
            else:
                payload = {
                    "equipment_tag": equipment_tag,
                    "message": reason,
                    "site_id": site_id,
                }

            rollback = policy.rollback_guidance or "Contact site systems administrator for manual rollback."

            if dry_run:
                triggered_actions.append({
                    "policy_id": policy.policy_id,
                    "policy_name": policy.name,
                    "action_type": policy.action_type,
                    "target_system": policy.target_system,
                    "approval_threshold": policy.approval_threshold,
                    "status": "SIMULATED_PENDING_APPROVAL" if policy.approval_threshold == "REQUIRES_APPROVAL" else "SIMULATED_AUTONOMOUS_EXECUTE",
                    "payload": payload,
                    "rollback_guidance": rollback,
                    "dry_run": True,
                })
            else:
                if policy.approval_threshold == "REQUIRES_APPROVAL":
                    approval = ApprovalRecord(
                        action_type=policy.action_type,
                        target_system=policy.target_system,
                        payload_json=json.dumps(payload),
                        requested_by=user_id,
                        site_id=site_id,
                        status="PENDING",
                        rollback_guidance=rollback,
                    )
                    db.add(approval)
                    db.flush()

                    audit = AuditEvent(
                        user_id=user_id,
                        site_id=site_id,
                        role="AutomationEngine",
                        action_type="AUTOMATION_QUEUED_FOR_APPROVAL",
                        resource_type="approval_record",
                        resource_id=approval.approval_id,
                        details_json=json.dumps({"policy_id": policy.policy_id, "equipment_tag": equipment_tag}),
                        status="SUCCESS",
                    )
                    db.add(audit)
                    db.commit()

                    triggered_actions.append({
                        "policy_id": policy.policy_id,
                        "policy_name": policy.name,
                        "approval_id": approval.approval_id,
                        "action_type": policy.action_type,
                        "target_system": policy.target_system,
                        "approval_threshold": policy.approval_threshold,
                        "status": "QUEUED_FOR_APPROVAL",
                        "payload": payload,
                        "rollback_guidance": rollback,
                        "dry_run": False,
                    })
                else:
                    # Autonomous execute
                    approval = ApprovalRecord(
                        action_type=policy.action_type,
                        target_system=policy.target_system,
                        payload_json=json.dumps(payload),
                        requested_by=user_id,
                        site_id=site_id,
                        status="AUTONOMOUS_EXECUTED",
                        rollback_guidance=rollback,
                        reviewed_by="SYSTEM_AUTONOMOUS",
                        reviewed_at=datetime.now(timezone.utc),
                    )
                    db.add(approval)
                    db.flush()

                    audit = AuditEvent(
                        user_id=user_id,
                        site_id=site_id,
                        role="AutomationEngine",
                        action_type="AUTOMATION_AUTONOMOUS_EXECUTED",
                        resource_type="approval_record",
                        resource_id=approval.approval_id,
                        details_json=json.dumps({"policy_id": policy.policy_id, "equipment_tag": equipment_tag}),
                        status="SUCCESS",
                    )
                    db.add(audit)
                    db.commit()

                    triggered_actions.append({
                        "policy_id": policy.policy_id,
                        "policy_name": policy.name,
                        "approval_id": approval.approval_id,
                        "action_type": policy.action_type,
                        "target_system": policy.target_system,
                        "approval_threshold": policy.approval_threshold,
                        "status": "EXECUTED_AUTONOMOUSLY",
                        "payload": payload,
                        "rollback_guidance": rollback,
                        "dry_run": False,
                    })

    return {
        "trigger_type": trigger_type,
        "site_id": site_id,
        "matched_policies_count": len(policies),
        "triggered_count": len(triggered_actions),
        "dry_run": dry_run,
        "actions": triggered_actions,
    }


def list_pending_approvals(db: Session, site_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    """List approval queue records."""
    query = db.query(ApprovalRecord)
    if site_id:
        query = query.filter(ApprovalRecord.site_id == site_id)
    if status:
        query = query.filter(ApprovalRecord.status == status)
    records = query.order_by(ApprovalRecord.created_at.desc()).all()
    return [r.to_dict() for r in records]


def review_approval(
    db: Session,
    approval_id: str,
    action: str,  # "APPROVED" or "REJECTED"
    reviewed_by: str,
    review_notes: str | None = None,
) -> dict[str, Any] | None:
    """Operator approval or rejection of queued automation action."""
    approval = db.query(ApprovalRecord).filter(ApprovalRecord.approval_id == approval_id).first()
    if not approval:
        return None

    if approval.status != "PENDING":
        return approval.to_dict()

    action_upper = action.upper()
    approval.status = action_upper
    approval.reviewed_by = reviewed_by
    approval.reviewed_at = datetime.now(timezone.utc)

    audit = AuditEvent(
        user_id=reviewed_by,
        site_id=approval.site_id,
        role="ReliabilityLead",
        action_type=f"APPROVAL_{action_upper}",
        resource_type="approval_record",
        resource_id=approval.approval_id,
        details_json=json.dumps({"notes": review_notes or "", "target_system": approval.target_system}),
        status="SUCCESS",
    )
    db.add(audit)
    db.commit()
    db.refresh(approval)
    return approval.to_dict()
