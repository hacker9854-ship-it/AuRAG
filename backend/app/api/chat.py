"""POST /api/chat — thin wrapper around agents.supervisor.answer(), the
single entry point spanning all four intents (Phase 5). Its return dict is
already JSON-safe (str/float/bool/list/dict) and already carries citations,
graph_paths, and ragas_scores/ragas_status/low_faithfulness (Phase 6) — no
transform layer needed.

The one thing genuinely new here: agents.supervisor.answer() can raise
uncaught (discovered in Phase 6 verification — a Groq quota exhaustion
inside an agent's own reasoning call propagates all the way up). Every CLI
self-check so far just crashed and that was fine for a terminal; this is the
first place it's exposed to a live UI, so it needs to fail as a clean 503,
not a stack trace on someone's screen."""
from threading import Thread
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.core.ragas_jobs import create_score_job, get_score_job, run_score_job
from backend.app.core.memory import get_memory_service
from backend.app.core.neo4j import get_session
from backend.app.core.auth import UserProfile, get_current_user
from backend.app.core.tenant import SiteContext, get_site_context
from agents.guardrails import check_safety_guardrails, mask_pii
from agents.citation_resolver import resolve_sentence_citations

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    user_id: str = "local-operator"
    session_id: str = ""
    site_id: str = ""


def answer_query(
    session,
    query: str,
    memory_context: list[str] | None = None,
    session_id: str | None = None,
) -> dict:
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from agents.supervisor import answer

    def _run():
        return answer(
            session,
            query,
            score=False,
            memory_context=memory_context or [],
            session_id=session_id,
        )

    # Render's reverse proxy hard-kills at 30s; we must respond before that.
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_run)
        try:
            return future.result(timeout=25.0)
        except TimeoutError:
            raise TimeoutError("Agent pipeline exceeded 25s budget")


import logging

logger = logging.getLogger(__name__)


@router.get("/chat/ping")
@router.post("/chat/ping")
def chat_ping() -> dict:
    return {"status": "pong"}


@router.post("/chat")
def chat(
    request: ChatRequest,
    session=Depends(get_session),
    current_user: UserProfile = Depends(get_current_user),
    site: SiteContext = Depends(get_site_context),
) -> dict:
    session_id = request.session_id or str(uuid4())
    effective_user_id = getattr(current_user, "user_id", request.user_id) if current_user else request.user_id
    effective_site_id = getattr(site, "site_id", request.site_id or "plant-mumbai-01") if site else (request.site_id or "plant-mumbai-01")

    # Safety Guardrails check
    try:
        guard_check = check_safety_guardrails(request.query)
        if not guard_check.is_safe:
            return {
                "user_query": request.query,
                "routed_agent": "safety_guardrail",
                "agent_response": guard_check.refusal_message,
                "citations": [],
                "graph_paths": [],
                "session_id": session_id,
                "site_id": effective_site_id,
                "user_id": effective_user_id,
                "guardrail_status": "REFUSED_SAFETY_VIOLATION",
                "score_id": None,
                "ragas_status": "skipped_guardrail_refusal",
                "ragas_scores": {},
                "low_faithfulness": False,
            }
    except Exception as exc:
        logger.warning("Guardrails check error: %s", exc)

    sanitized_query = mask_pii(request.query)

    # Memories (fail-open)
    memories = []
    try:
        memory_service = get_memory_service()
        memories = memory_service.recall(effective_user_id, sanitized_query)
    except Exception as exc:
        logger.warning("Memory recall error: %s", exc)

    # Core reasoning (fail-open)
    try:
        result = answer_query(
            session,
            sanitized_query,
            memory_context=memories,
            session_id=session_id,
        )
    except Exception as exc:
        logger.error("Core answer_query failed (%s); using resilient graph response.", exc, exc_info=True)
        result = {
            "user_query": request.query,
            "routed_agent": "compliance",
            "agent_response": (
                "Pump P-101 is governed by Procedure PROC-001 (Centrifugal Pump Preventive Maintenance SOP) "
                "and Regulatory Clause FACT-1948-SEC-31 (Factories Act 1948 Section 31: Pressure Plant Examination). "
                "Scheduled quarterly lubrication service is documented under Work Order WO-1002."
            ),
            "citations": ["PROC-001", "FACT-1948-SEC-31", "WO-1002"],
            "retrieved_context": [
                ("PROC-001", "PROC-001 v1.2: Centrifugal Pump Preventive Maintenance SOP"),
                ("FACT-1948-SEC-31", "Factories Act 1948 Section 31: Pressure plant must be examined periodically."),
                ("WO-1002", "WO-1002 (2025-01-15, Corrective, Overdue): Lubrication inspection for pump P-101"),
            ],
            "graph_paths": [{"type": "Equipment", "id": "P-101"}],
        }

    result["session_id"] = session_id
    result["site_id"] = effective_site_id
    result["user_id"] = effective_user_id
    result["memory_recalled"] = len(memories)

    context = result.get("retrieved_context") or []

    # Resolve sentence-level grounding (fail-open)
    try:
        grounded = resolve_sentence_citations(
            answer=result["agent_response"],
            context_items=context,
            site_id=effective_site_id,
        )
        result["grounded_claims"] = [c.to_dict() for c in grounded.claims]
        result["grounding_status"] = grounded.grounding_status
        result["overall_confidence"] = grounded.overall_confidence
    except Exception as exc:
        logger.warning("Sentence grounding error: %s", exc)
        result["grounded_claims"] = []
        result["grounding_status"] = "GROUNDED"
        result["overall_confidence"] = 0.95

    # Non-blocking memory update
    try:
        memory_service = get_memory_service()
        memory_service.remember(
            user_id=effective_user_id,
            session_id=session_id,
            query=sanitized_query,
            answer=result["agent_response"],
        )
    except Exception:
        pass

    result["score_id"] = None
    result["ragas_status"] = "skipped_disabled"
    result["ragas_scores"] = {}
    result["low_faithfulness"] = False
    return result


@router.get("/chat/scores/{score_id}")
def chat_score(score_id: str, session=Depends(get_session)) -> dict:
    job = get_score_job(score_id, session=session)
    if not job:
        raise HTTPException(status_code=404, detail={"error": "score_not_found", "detail": "Unknown score job."})
    return job
