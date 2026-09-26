"""Durable RAGAS evaluation history and aggregate dashboard endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.neo4j import get_session
from backend.app.services.evaluations import (
    count_evaluations,
    get_evaluation,
    list_evaluations,
    summarize_evaluations_db,
)

router = APIRouter()


@router.get("/evaluations")
def evaluation_results(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    agent: str | None = None,
    low_faithfulness: bool | None = None,
    session=Depends(get_session),
) -> dict:
    if limit < 1 or limit > 200 or offset < 0:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_pagination",
                "detail": "limit must be 1-200 and offset must be non-negative.",
            },
        )
    try:
        total = count_evaluations(
            session,
            status=status,
            agent=agent,
            low_faithfulness=low_faithfulness,
        )
        return {
            "items": list_evaluations(
                session,
                limit=limit,
                offset=offset,
                status=status,
                agent=agent,
                low_faithfulness=low_faithfulness,
            ),
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": offset + limit < total,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "evaluations_failed", "detail": str(exc)},
        ) from exc


@router.get("/evaluations/summary")
def evaluation_summary(session=Depends(get_session)) -> dict:
    try:
        return summarize_evaluations_db(session)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "evaluation_summary_failed", "detail": str(exc)},
        ) from exc


@router.get("/evaluations/{score_id}")
def evaluation_detail(score_id: str, session=Depends(get_session)) -> dict:
    try:
        result = get_evaluation(session, score_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "evaluation_not_found",
                    "detail": f"No evaluation found for {score_id}.",
                },
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "evaluation_failed", "detail": str(exc)},
        ) from exc
