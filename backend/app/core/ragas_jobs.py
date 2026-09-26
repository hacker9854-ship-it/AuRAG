"""Asynchronous RAGAS jobs with a Neo4j-backed durable record."""

from datetime import datetime, timezone
from threading import Lock
from time import perf_counter
from uuid import uuid4

from backend.app.services.evaluations import (
    create_evaluation,
    get_evaluation,
    update_evaluation,
)

_JOBS: dict[str, dict] = {}
_LOCK = Lock()


def _public_job(job: dict) -> dict:
    return {
        "score_id": job["score_id"],
        "ragas_status": job["ragas_status"],
        "ragas_scores": job.get("ragas_scores") or {},
        "low_faithfulness": bool(job.get("low_faithfulness")),
        "detail": job.get("detail"),
    }


def create_score_job(
    session,
    *,
    query: str,
    agent_response: str,
    routed_agent: str,
    citations: list[str],
    graph_paths: list[dict],
    retrieved_context: list,
) -> str:
    score_id = str(uuid4())
    create_evaluation(
        session,
        score_id=score_id,
        query=query,
        answer=agent_response,
        routed_agent=routed_agent,
        citations=citations,
        graph_paths=graph_paths,
        retrieved_context=retrieved_context,
    )
    with _LOCK:
        _JOBS[score_id] = {
            "score_id": score_id,
            "ragas_status": "scoring",
            "ragas_scores": {},
            "low_faithfulness": False,
        }
    return score_id


def _persist_result(score_id: str, update: dict, duration_ms: int) -> None:
    from retrieval.index_chunks import get_database, get_driver

    db = get_database()
    driver = get_driver()
    session = driver.session(database=db) if db else driver.session()
    with session:
        update_evaluation(
            session,
            score_id,
            status=update["ragas_status"],
            scores=update.get("ragas_scores"),
            low_faithfulness=update.get("low_faithfulness", False),
            duration_ms=duration_ms,
            completed_at=datetime.now(timezone.utc).isoformat(),
            detail=update.get("detail"),
        )



def run_score_job(
    score_id: str,
    user_query: str,
    agent_response: str,
    retrieved_context: list,
) -> None:
    started = perf_counter()
    try:
        from evaluation.score import score_answer

        result = score_answer(user_query, agent_response, retrieved_context)
        update = {
            "ragas_status": "scored",
            "ragas_scores": {
                "faithfulness": result["faithfulness"],
                "context_precision": result["context_precision"],
                "answer_relevancy": result["answer_relevancy"],
            },
            "low_faithfulness": result["low_faithfulness"],
        }
    except Exception as exc:
        print(f"[evaluation.score] async scoring failed, answer already returned: {exc}")
        update = {
            "ragas_status": "error",
            "ragas_scores": {},
            "low_faithfulness": False,
            "detail": str(exc),
        }

    duration_ms = round((perf_counter() - started) * 1000)
    try:
        _persist_result(score_id, update, duration_ms)
    except Exception as exc:
        print(f"[evaluation.store] durable update failed: {exc}")
        update = {
            **update,
            "detail": (
                f"{update.get('detail')}; durable update failed: {exc}"
                if update.get("detail")
                else f"durable update failed: {exc}"
            ),
        }

    with _LOCK:
        job = _JOBS.get(score_id)
        if job is not None:
            job.update(update)

def get_score_job(score_id: str, session=None) -> dict | None:
    with _LOCK:
        job = _JOBS.get(score_id)
        if job is not None:
            return _public_job(job)

    if session is not None:
        durable = get_evaluation(session, score_id)
    else:
        from retrieval.index_chunks import get_database, get_driver

        with get_driver().session(database=get_database()) as durable_session:
            durable = get_evaluation(durable_session, score_id)

    return _public_job(durable) if durable else None
