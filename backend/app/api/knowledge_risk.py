"""Knowledge-retirement risk endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.neo4j import get_session
from backend.app.services.knowledge_risk import (
    get_person_knowledge_risk,
    list_knowledge_risks,
)

router = APIRouter()


def _validate_horizon(retirement_horizon: int) -> None:
    if retirement_horizon < 1 or retirement_horizon > 30:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_retirement_horizon",
                "detail": "retirement_horizon must be between 1 and 30 years.",
            },
        )


@router.get("/knowledge-risk")
def knowledge_risks(
    retirement_horizon: int = 5,
    session=Depends(get_session),
) -> dict:
    _validate_horizon(retirement_horizon)
    try:
        return list_knowledge_risks(session, retirement_horizon=retirement_horizon)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "knowledge_risk_failed", "detail": str(exc)},
        ) from exc


@router.get("/knowledge-risk/people/{person_id}")
def person_knowledge_risk(
    person_id: str,
    retirement_horizon: int = 5,
    session=Depends(get_session),
) -> dict:
    _validate_horizon(retirement_horizon)
    try:
        result = get_person_knowledge_risk(
            session,
            person_id=person_id,
            retirement_horizon=retirement_horizon,
        )
        if result is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "person_not_found",
                    "detail": f"No Person found for {person_id}.",
                },
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "knowledge_risk_failed", "detail": str(exc)},
        ) from exc

