"""Audit logging service providing tamper-evident operational recording."""
import json
import logging
from typing import Any
from sqlalchemy.orm import Session
from backend.app.db.models import AuditEvent

logger = logging.getLogger(__name__)


def log_audit_event(
    db: Session,
    user_id: str,
    site_id: str,
    role: str,
    action_type: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    status: str = "SUCCESS",
    ip_address: str | None = None,
) -> AuditEvent:
    """Synchronously record an immutable audit event to the relational database."""
    try:
        details_str = json.dumps(details or {}, default=str)
        event = AuditEvent(
            user_id=user_id,
            site_id=site_id,
            role=role,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details_json=details_str,
            status=status,
            ip_address=ip_address,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    except Exception as exc:
        db.rollback()
        logger.error("Failed to write audit event: %s", exc)
        raise


def query_audit_events(
    db: Session,
    site_id: str,
    limit: int = 50,
    offset: int = 0,
    action_type: str | None = None,
    user_id: str | None = None,
) -> list[dict]:
    """Retrieve audit events filtered by site boundary and optional criteria."""
    query = db.query(AuditEvent).filter(AuditEvent.site_id == site_id)
    if action_type:
        query = query.filter(AuditEvent.action_type == action_type)
    if user_id:
        query = query.filter(AuditEvent.user_id == user_id)

    query = query.order_by(AuditEvent.timestamp.desc()).offset(offset).limit(limit)
    events = query.all()
    return [e.to_dict() for e in events]
