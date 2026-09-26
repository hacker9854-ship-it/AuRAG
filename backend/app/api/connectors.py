"""Enterprise Connector Management, Freshness Monitoring, and Audit APIs."""
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.auth import AppRole, UserProfile, get_current_user, require_roles
from backend.app.core.tenant import SiteContext, get_site_context
from backend.app.db.database import get_db
from backend.app.db.models import AuditEvent, ConnectorSync, QuarantineItem
from backend.app.services.audit import log_audit_event, query_audit_events
from ingestion.connectors.osisoft_pi import OSIsoftPIConnector
from ingestion.connectors.qms import QMSConnector
from ingestion.connectors.sap_pm import SAPPMConnector
from ingestion.connectors.sharepoint import SharePointConnector

router = APIRouter(tags=["Enterprise Connectors & Audit"])
logger = logging.getLogger(__name__)

# Registry of available connector instances
CONNECTOR_REGISTRY = {
    "sap_pm": SAPPMConnector(connector_id="sap_pm"),
    "osisoft_pi": OSIsoftPIConnector(connector_id="osisoft_pi"),
    "sharepoint": SharePointConnector(connector_id="sharepoint"),
    "qms": QMSConnector(connector_id="qms"),
}


class QuarantineReviewRequest(BaseModel):
    decision: str  # "APPROVED" or "REJECTED"
    notes: str = ""


@router.get("/connectors")
def list_connectors(
    db: Session = Depends(get_db),
    site: SiteContext = Depends(get_site_context),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """List all enterprise connectors, health status, and sync telemetry."""
    site_id = site.site_id if isinstance(site, SiteContext) else "plant-mumbai-01"
    results = []

    for conn_id, conn in CONNECTOR_REGISTRY.items():
        # Query latest sync state from DB
        sync_rec = (
            db.query(ConnectorSync)
            .filter(ConnectorSync.connector_id == conn_id, ConnectorSync.site_id == site_id)
            .first()
        )
        is_healthy = conn.health_check()
        results.append({
            "connector_id": conn_id,
            "source_type": conn.source_type,
            "site_id": site_id,
            "health_status": "UP" if is_healthy else "DOWN",
            "last_sync_at": sync_rec.last_sync_at.isoformat() if sync_rec and sync_rec.last_sync_at else None,
            "records_synced": sync_rec.records_synced if sync_rec else 0,
            "status": sync_rec.status if sync_rec else "IDLE",
        })

    return {"connectors": results, "site_id": site_id}


@router.post("/connectors/{connector_id}/sync")
def trigger_connector_sync(
    connector_id: str,
    db: Session = Depends(get_db),
    site: SiteContext = Depends(get_site_context),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Trigger on-demand synchronization for a specific enterprise connector."""
    conn = CONNECTOR_REGISTRY.get(connector_id)
    if not conn:
        raise HTTPException(status_code=404, detail={"error": "not_found", "detail": f"Unknown connector '{connector_id}'"})

    site_id = site.site_id if isinstance(site, SiteContext) else "plant-mumbai-01"
    user_id = current_user.user_id if isinstance(current_user, UserProfile) else "local-operator"
    role = current_user.roles[0] if isinstance(current_user, UserProfile) and current_user.roles else "PlantOperator"

    # Execute sync
    sync_result = conn.sync()

    # Upsert connector state in relational DB
    sync_rec = (
        db.query(ConnectorSync)
        .filter(ConnectorSync.connector_id == connector_id, ConnectorSync.site_id == site_id)
        .first()
    )
    if not sync_rec:
        sync_rec = ConnectorSync(
            connector_id=connector_id,
            source_type=conn.source_type,
            site_id=site_id,
            records_synced=0,
        )
        db.add(sync_rec)

    current_count = sync_rec.records_synced or 0
    sync_rec.records_synced = current_count + sync_result.records_synced
    sync_rec.status = "HEALTHY" if sync_result.success else "FAILED"
    sync_rec.cursor_token = sync_result.new_cursor
    db.commit()

    # Log immutable audit event
    log_audit_event(
        db=db,
        user_id=user_id,
        site_id=site_id,
        role=role,
        action_type="CONNECTOR_SYNC",
        resource_type="CONNECTOR",
        resource_id=connector_id,
        details={
            "records_synced": sync_result.records_synced,
            "source_type": conn.source_type,
            "cursor": sync_result.new_cursor,
        },
    )

    return {
        "connector_id": connector_id,
        "status": "COMPLETED",
        "records_synced": sync_result.records_synced,
        "cursor": sync_result.new_cursor,
        "sample_records": sync_result.records[:3],
    }


@router.get("/connectors/quarantine")
def list_quarantine_items(
    db: Session = Depends(get_db),
    site: SiteContext = Depends(get_site_context),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """List documents and records currently held in quarantine."""
    items = db.query(QuarantineItem).order_by(QuarantineItem.created_at.desc()).limit(100).all()
    return {"quarantine_items": [item.to_dict() for item in items]}


@router.post("/connectors/quarantine/{item_id}/review")
def review_quarantine_item(
    item_id: str,
    request: QuarantineReviewRequest,
    db: Session = Depends(get_db),
    site: SiteContext = Depends(get_site_context),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Approve or reject a quarantined document."""
    item = db.query(QuarantineItem).filter(QuarantineItem.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail={"error": "not_found", "detail": f"Quarantine item '{item_id}' not found"})

    user_id = current_user.user_id if isinstance(current_user, UserProfile) else "local-operator"
    role = current_user.roles[0] if isinstance(current_user, UserProfile) and current_user.roles else "PlantOperator"
    site_id = site.site_id if isinstance(site, SiteContext) else "plant-mumbai-01"

    decision = request.decision.upper()
    if decision not in ("APPROVED", "REJECTED"):
        raise HTTPException(status_code=400, detail={"error": "bad_request", "detail": "Decision must be APPROVED or REJECTED"})

    item.status = decision
    item.reviewed_by = user_id
    item.review_notes = request.notes
    db.commit()

    # Log audit event
    log_audit_event(
        db=db,
        user_id=user_id,
        site_id=site_id,
        role=role,
        action_type="QUARANTINE_REVIEW",
        resource_type="DOCUMENT",
        resource_id=item.filename,
        details={"decision": decision, "item_id": item_id, "notes": request.notes},
    )

    return {"item_id": item_id, "status": item.status, "reviewed_by": user_id}


@router.get("/audit/events")
def get_audit_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action_type: str | None = None,
    db: Session = Depends(get_db),
    site: SiteContext = Depends(get_site_context),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Retrieve immutable audit events scoped by site context."""
    site_id = site.site_id if isinstance(site, SiteContext) else "plant-mumbai-01"
    events = query_audit_events(
        db=db,
        site_id=site_id,
        limit=limit,
        offset=offset,
        action_type=action_type,
    )
    return {"site_id": site_id, "total_returned": len(events), "events": events}
