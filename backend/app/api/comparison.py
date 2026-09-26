"""GraphRAG versus plain dense-vector RAG comparison endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.core.neo4j import get_session
from backend.app.services.comparison import compare_answers

router = APIRouter()


class ComparisonRequest(BaseModel):
    query: str


@router.post("/comparison")
def comparison(request: ComparisonRequest, session=Depends(get_session)) -> dict:
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=422,
            detail={"error": "invalid_query", "detail": "query must not be blank."},
        )
    try:
        return compare_answers(session, query)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "comparison_failed", "detail": str(exc)},
        ) from exc

