"""Persistent work-order workflow endpoints."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.core.neo4j import get_session
from backend.app.services.work_orders import (
    InvalidWorkOrderTransition,
    WorkOrderConflict,
    WorkOrderNotFound,
    create_draft_work_order,
    decide_work_order,
    get_work_order,
    list_work_orders,
    update_work_order,
)

router = APIRouter()


class WorkOrderDraftRequest(BaseModel):
    equipment_tag: str
    event_id: str | None = None
    description: str
    recommended_action: str
    actor: str = "local-operator"


class WorkOrderEditRequest(BaseModel):
    expected_version: int
    description: str
    recommended_action: str
    actor: str = "local-operator"


class WorkOrderDecisionRequest(BaseModel):
    decision: Literal["accept", "reject"]
    actor: str = "local-operator"
    expected_version: int
    reason: str | None = None


def _map_domain_error(exc: Exception) -> HTTPException:
    if isinstance(exc, WorkOrderNotFound):
        return HTTPException(
            status_code=404,
            detail={"error": "work_order_not_found", "detail": str(exc)},
        )
    if isinstance(exc, WorkOrderConflict):
        return HTTPException(
            status_code=409,
            detail={"error": "work_order_conflict", "detail": str(exc)},
        )
    if isinstance(exc, (InvalidWorkOrderTransition, ValueError)):
        return HTTPException(
            status_code=422,
            detail={"error": "invalid_work_order_decision", "detail": str(exc)},
        )
    return HTTPException(
        status_code=503,
        detail={"error": "work_order_failed", "detail": str(exc)},
    )


@router.get("/work-orders")
def work_order_list(
    status: str | None = None,
    limit: int = 100,
    session=Depends(get_session),
) -> dict:
    if limit < 1 or limit > 200:
        raise HTTPException(
            status_code=422,
            detail={"error": "invalid_limit", "detail": "limit must be 1-200."},
        )
    try:
        return {"items": list_work_orders(session, status=status, limit=limit)}
    except Exception as exc:
        raise _map_domain_error(exc) from exc


@router.post("/work-orders/drafts")
def create_draft(
    request: WorkOrderDraftRequest,
    session=Depends(get_session),
) -> dict:
    try:
        return create_draft_work_order(
            session,
            equipment_tag=request.equipment_tag,
            event_id=request.event_id,
            description=request.description.strip(),
            recommended_action=request.recommended_action.strip(),
            actor=request.actor,
        )
    except Exception as exc:
        raise _map_domain_error(exc) from exc


@router.get("/work-orders/{work_order_id}")
def work_order_detail(work_order_id: str, session=Depends(get_session)) -> dict:
    try:
        result = get_work_order(session, work_order_id)
        if result is None:
            raise WorkOrderNotFound(work_order_id)
        return result
    except Exception as exc:
        raise _map_domain_error(exc) from exc


@router.patch("/work-orders/{work_order_id}")
def edit_work_order(
    work_order_id: str,
    request: WorkOrderEditRequest,
    session=Depends(get_session),
) -> dict:
    try:
        return update_work_order(
            session,
            work_order_id,
            expected_version=request.expected_version,
            description=request.description.strip(),
            recommended_action=request.recommended_action.strip(),
            actor=request.actor,
        )
    except Exception as exc:
        raise _map_domain_error(exc) from exc


@router.post("/work-orders/{work_order_id}/decisions")
def decide(
    work_order_id: str,
    request: WorkOrderDecisionRequest,
    session=Depends(get_session),
) -> dict:
    try:
        return decide_work_order(
            session,
            work_order_id,
            decision=request.decision,
            actor=request.actor,
            expected_version=request.expected_version,
            reason=request.reason,
        )
    except Exception as exc:
        raise _map_domain_error(exc) from exc

