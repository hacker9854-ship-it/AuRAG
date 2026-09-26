"""Enterprise Automation, Human-in-the-Loop Governance, and Evaluation Remediation APIs."""
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.auth import UserProfile, get_current_user
from backend.app.core.tenant import SiteContext, get_site_context
from backend.app.db.database import get_db
from backend.app.services.automation import (
    create_or_update_policy,
    evaluate_automation_trigger,
    list_automation_policies,
    list_pending_approvals,
    review_approval,
)
from backend.app.services.evaluations import (
    create_remediation,
    list_remediations,
    update_remediation_status,
)

router = APIRouter(prefix="/automations", tags=["Enterprise Automation & Governance"])
logger = logging.getLogger(__name__)


class PolicyUpsertRequest(BaseModel):
    policy_id: str | None = None
    site_id: str = "*"
    name: str
    description: str | None = None
    trigger_type: str
    action_type: str
    target_system: str
    approval_threshold: str = "REQUIRES_APPROVAL"
    parameters: dict[str, Any] = {}
    rollback_guidance: str | None = None
    is_active: bool = True


class AutomationEvaluateRequest(BaseModel):
    trigger_type: str
    context_data: dict[str, Any]
    dry_run: bool = False


class ApprovalReviewRequest(BaseModel):
    action: str  # "APPROVED" or "REJECTED"
    notes: str = ""


class RemediationCreateRequest(BaseModel):
    score_id: str
    reason: str
    incorrect_snippets: list[str] = []
    correction_notes: str


class RemediationStatusRequest(BaseModel):
    status: str  # "PENDING_REINDEX", "REINDEXED", "RESOLVED"


@router.get("/policies")
def get_policies(
    db: Session = Depends(get_db),
    site: SiteContext = Depends(get_site_context),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """List site-scoped automation policies."""
    site_id = site.site_id if isinstance(site, SiteContext) else "plant-mumbai-01"
    policies = list_automation_policies(db, site_id=site_id)
    return {"policies": policies, "total": len(policies), "site_id": site_id}


@router.post("/policies")
def upsert_policy(
    req: PolicyUpsertRequest,
    db: Session = Depends(get_db),
    site: SiteContext = Depends(get_site_context),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Create or update an automation policy."""
    policy_data = req.model_dump()
    if policy_data.get("site_id") == "*" and hasattr(site, "site_id") and site.site_id != "plant-mumbai-01":
        policy_data["site_id"] = site.site_id

    result = create_or_update_policy(db, policy_data, user_id=current_user.user_id)
    return {"status": "SUCCESS", "policy": result}


@router.post("/evaluate")
def evaluate_trigger(
    req: AutomationEvaluateRequest,
    db: Session = Depends(get_db),
    site: SiteContext = Depends(get_site_context),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Evaluate an equipment health event or compliance gap against automation policies.
    Supports dry-run simulation mode without modifying system state.
    """
    site_id = site.site_id if isinstance(site, SiteContext) else "plant-mumbai-01"
    result = evaluate_automation_trigger(
        db=db,
        trigger_type=req.trigger_type,
        site_id=site_id,
        context_data=req.context_data,
        user_id=current_user.user_id,
        dry_run=req.dry_run,
    )
    return result


@router.get("/queue")
def get_approval_queue(
    status: str | None = Query(None, description="Filter by approval status: PENDING, APPROVED, REJECTED"),
    db: Session = Depends(get_db),
    site: SiteContext = Depends(get_site_context),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """List pending or reviewed automation approval records."""
    site_id = site.site_id if isinstance(site, SiteContext) else "plant-mumbai-01"
    records = list_pending_approvals(db, site_id=site_id, status=status)
    return {"queue": records, "total": len(records), "site_id": site_id}


@router.post("/queue/{approval_id}/action")
def take_approval_action(
    approval_id: str,
    req: ApprovalReviewRequest,
    db: Session = Depends(get_db),
    site: SiteContext = Depends(get_site_context),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Approve or reject a queued automation action."""
    action = req.action.upper()
    if action not in ("APPROVED", "REJECTED"):
        raise HTTPException(status_code=400, detail="Action must be either APPROVED or REJECTED")

    result = review_approval(
        db=db,
        approval_id=approval_id,
        action=action,
        reviewed_by=current_user.user_id,
        review_notes=req.notes,
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"Approval record '{approval_id}' not found")

    return {"status": "SUCCESS", "approval": result}


# Evaluation Remediation Endpoints
@router.get("/remediations")
def get_remediations(
    status: str | None = Query(None, description="Filter by remediation status: PENDING_REINDEX, REINDEXED, RESOLVED"),
    db: Session = Depends(get_db),
    site: SiteContext = Depends(get_site_context),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """List operational evaluation remediation items."""
    site_id = site.site_id if isinstance(site, SiteContext) else "plant-mumbai-01"
    items = list_remediations(db, site_id=site_id, status=status)
    return {"remediations": items, "total": len(items), "site_id": site_id}


@router.post("/remediations")
def submit_remediation(
    req: RemediationCreateRequest,
    db: Session = Depends(get_db),
    site: SiteContext = Depends(get_site_context),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Flag an answer or evidence chunk as incorrect and queue for re-indexing."""
    site_id = site.site_id if isinstance(site, SiteContext) else "plant-mumbai-01"
    remediation = create_remediation(
        db=db,
        score_id=req.score_id,
        user_id=current_user.user_id,
        site_id=site_id,
        reason=req.reason,
        incorrect_snippets=req.incorrect_snippets,
        correction_notes=req.correction_notes,
    )
    return {"status": "SUCCESS", "remediation": remediation}


@router.post("/remediations/{remediation_id}/status")
def change_remediation_status(
    remediation_id: str,
    req: RemediationStatusRequest,
    db: Session = Depends(get_db),
    site: SiteContext = Depends(get_site_context),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Update status of a remediation request."""
    status = req.status.upper()
    if status not in ("PENDING_REINDEX", "REINDEXED", "RESOLVED"):
        raise HTTPException(status_code=400, detail="Invalid remediation status")

    updated = update_remediation_status(
        db=db,
        remediation_id=remediation_id,
        status=status,
        resolved_by=current_user.user_id,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Remediation '{remediation_id}' not found")

    return {"status": "SUCCESS", "remediation": updated}
