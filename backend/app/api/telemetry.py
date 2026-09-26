"""Telemetry scanning plus durable predictive-event/work-order creation."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.core.neo4j import get_session
from backend.app.services.events import create_predictive_event, publish_event
from backend.app.services.work_orders import create_draft_work_order

router = APIRouter()


def generate_reading(*args, **kwargs):
    from telemetry.generator import generate_reading as implementation

    return implementation(*args, **kwargs)


def meta_for(*args, **kwargs):
    from telemetry.generator import meta_for as implementation

    return implementation(*args, **kwargs)


def match_reading(*args, **kwargs):
    from telemetry.pattern_match import match_reading as implementation

    return implementation(*args, **kwargs)


def build_warning(*args, **kwargs):
    from telemetry.draft import build_warning as implementation

    return implementation(*args, **kwargs)


def draft_work_order(*args, **kwargs):
    from telemetry.draft import draft_work_order as implementation

    return implementation(*args, **kwargs)


class ScanRequest(BaseModel):
    equipment_tag: str
    drift_toward: str | None = None
    drift_pct: float = 0.0


@router.post("/telemetry/scan")
def scan(request: ScanRequest, session=Depends(get_session)) -> dict:
    try:
        reading = generate_reading(
            session,
            request.equipment_tag,
            drift_toward=request.drift_toward,
            drift_pct=request.drift_pct,
        )
        matches = match_reading(session, request.equipment_tag, reading)
        warning = build_warning(request.equipment_tag, matches)
        reading_meta = meta_for(key for key in reading if key != "equipment")
        predictive_event = None

        if warning:
            predictive_event = create_predictive_event(
                session,
                equipment_tag=request.equipment_tag,
                failure_event_id=warning["matched_failure_event"],
                similarity=warning["similarity"],
                symptom=warning["symptom"],
                reading=reading,
            )
            event_id = predictive_event["id"]
            warning = {**warning, "event_id": event_id}
            if predictive_event.get("_created", True):
                publish_event(event_id)

        return {
            "reading": reading,
            "reading_meta": reading_meta,
            "matches": matches,
            "warning": warning,
            "predictive_event": predictive_event,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "telemetry_scan_failed", "detail": str(exc)},
        ) from exc


class DraftRequest(BaseModel):
    equipment_tag: str
    top_match: dict
    event_id: str | None = None
    actor: str = "local-operator"


@router.post("/telemetry/draft")
def draft(request: DraftRequest, session=Depends(get_session)) -> dict:
    try:
        preview = draft_work_order(session, request.equipment_tag, request.top_match)
        return create_draft_work_order(
            session,
            equipment_tag=request.equipment_tag,
            event_id=request.event_id,
            description=preview["description"],
            recommended_action=preview["recommended_action"],
            actor=request.actor,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "telemetry_draft_failed", "detail": str(exc)},
        ) from exc
