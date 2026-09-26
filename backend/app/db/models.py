"""Relational models for enterprise audit ledger, connector state, and quarantine review."""
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from backend.app.db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditEvent(Base):
    """Immutable audit trail for all operator queries, model actions, and work-order decisions.
    Satisfies OSHA 1910.119 Process Safety Management and ISO 45001 compliance standards.
    """
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), default=utcnow, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    site_id = Column(String(64), nullable=False, index=True)
    role = Column(String(64), nullable=False)
    action_type = Column(String(64), nullable=False, index=True)
    resource_type = Column(String(64), nullable=True)
    resource_id = Column(String(128), nullable=True)
    details_json = Column(Text, default="{}")
    status = Column(String(32), default="SUCCESS")
    ip_address = Column(String(64), nullable=True)

    def to_dict(self) -> dict:
        try:
            details = json.loads(self.details_json) if self.details_json else {}
        except Exception:
            details = {"raw": self.details_json}
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "site_id": self.site_id,
            "role": self.role,
            "action_type": self.action_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": details,
            "status": self.status,
            "ip_address": self.ip_address,
        }


class ConnectorSync(Base):
    """Tracks synchronization status, delta cursors, and lag across enterprise connectors."""
    __tablename__ = "connector_syncs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    connector_id = Column(String(64), unique=True, index=True, nullable=False)
    source_type = Column(String(32), nullable=False, index=True)  # SAP_PM, SHAREPOINT, OSISOFT_PI, QMS
    site_id = Column(String(64), nullable=False, index=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    cursor_token = Column(String(256), nullable=True)
    records_synced = Column(Integer, default=0)
    status = Column(String(32), default="IDLE")  # IDLE, SYNCING, HEALTHY, FAILED
    error_message = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "connector_id": self.connector_id,
            "source_type": self.source_type,
            "site_id": self.site_id,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "cursor_token": self.cursor_token,
            "records_synced": self.records_synced,
            "status": self.status,
            "error_message": self.error_message,
        }


class QuarantineItem(Base):
    """Quarantine review ledger for corrupted files, checksum duplicates, or low-confidence P&IDs."""
    __tablename__ = "quarantine_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String(64), unique=True, index=True, default=lambda: f"QRN-{uuid.uuid4().hex[:8]}")
    source_system = Column(String(32), nullable=False)
    filename = Column(String(256), nullable=False)
    sha256 = Column(String(64), index=True, nullable=False)
    quarantine_reason = Column(String(256), nullable=False)
    severity = Column(String(32), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(32), default="PENDING_REVIEW")  # PENDING_REVIEW, APPROVED, REJECTED
    created_at = Column(DateTime(timezone=True), default=utcnow)
    reviewed_by = Column(String(128), nullable=True)
    review_notes = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "source_system": self.source_system,
            "filename": self.filename,
            "sha256": self.sha256,
            "quarantine_reason": self.quarantine_reason,
            "severity": self.severity,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewed_by": self.reviewed_by,
            "review_notes": self.review_notes,
        }


class ApprovalRecord(Base):
    """Governance ledger for human-in-the-loop approvals before external system writes (e.g. SAP work orders)."""
    __tablename__ = "approval_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    approval_id = Column(String(64), unique=True, index=True, default=lambda: f"APP-{uuid.uuid4().hex[:8]}")
    action_type = Column(String(64), nullable=False)  # WORK_ORDER_WRITE, POLICY_CHANGE, PND_OVERRIDE
    target_system = Column(String(32), nullable=False)  # SAP_PM, QMS
    payload_json = Column(Text, nullable=False)
    requested_by = Column(String(128), nullable=False)
    site_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), default="PENDING")  # PENDING, APPROVED, REJECTED
    reviewed_by = Column(String(128), nullable=True)
    rollback_guidance = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        try:
            payload = json.loads(self.payload_json) if self.payload_json else {}
        except Exception:
            payload = {"raw": self.payload_json}
        return {
            "approval_id": self.approval_id,
            "action_type": self.action_type,
            "target_system": self.target_system,
            "payload": payload,
            "requested_by": self.requested_by,
            "site_id": self.site_id,
            "status": self.status,
            "reviewed_by": self.reviewed_by,
            "rollback_guidance": self.rollback_guidance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


class AutomationPolicy(Base):
    """Configurable enterprise automation rule governing automated writes to SAP PM or QMS."""
    __tablename__ = "automation_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(String(64), unique=True, index=True, nullable=False)
    site_id = Column(String(64), nullable=False, index=True, default="*")
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    trigger_type = Column(String(64), nullable=False, index=True)  # HEALTH_INDEX_CRITICAL, STATUTORY_OVERDUE, VIBRATION_SPIKE
    action_type = Column(String(64), nullable=False)  # CREATE_SAP_WORK_ORDER, LOG_QMS_CAPA, SEND_ALERT
    target_system = Column(String(32), nullable=False)  # SAP_PM, QMS, NOTIFY
    approval_threshold = Column(String(32), default="REQUIRES_APPROVAL")  # REQUIRES_APPROVAL, AUTONOMOUS
    parameters_json = Column(Text, default="{}")
    rollback_guidance = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def to_dict(self) -> dict:
        try:
            params = json.loads(self.parameters_json) if self.parameters_json else {}
        except Exception:
            params = {"raw": self.parameters_json}
        return {
            "policy_id": self.policy_id,
            "site_id": self.site_id,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type,
            "action_type": self.action_type,
            "target_system": self.target_system,
            "approval_threshold": self.approval_threshold,
            "parameters": params,
            "rollback_guidance": self.rollback_guidance,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EvaluationRemediation(Base):
    """Operational feedback and remediation queue for low-faithfulness or hallucinated answers."""
    __tablename__ = "evaluation_remediations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    remediation_id = Column(String(64), unique=True, index=True, default=lambda: f"REM-{uuid.uuid4().hex[:8]}")
    score_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    site_id = Column(String(64), nullable=False, index=True, default="plant-mumbai-01")
    reason = Column(String(128), nullable=False)
    incorrect_snippets_json = Column(Text, default="[]")
    correction_notes = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING_REINDEX", index=True)  # PENDING_REINDEX, REINDEXED, RESOLVED
    created_at = Column(DateTime(timezone=True), default=utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(128), nullable=True)

    def to_dict(self) -> dict:
        try:
            snippets = json.loads(self.incorrect_snippets_json) if self.incorrect_snippets_json else []
        except Exception:
            snippets = [self.incorrect_snippets_json]
        return {
            "remediation_id": self.remediation_id,
            "score_id": self.score_id,
            "user_id": self.user_id,
            "site_id": self.site_id,
            "reason": self.reason,
            "incorrect_snippets": snippets,
            "correction_notes": self.correction_notes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
        }
