"""Shared LangGraph state shape, pre-decided in Phase 1 NOTES.md as the single
source of truth for this shape. Not wired into an actual StateGraph until
Phase 5 (Supervisor) — Phase 4 agents each return a plain dict populating the
subset of these keys they own (agent_response/citations/graph_paths/
retrieved_context); intent/routing_confidence/session_id/messages/
ragas_scores are owned by the Supervisor (Phase 5) and eval layer (Phase 6)."""
from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_query: str
    intent: str  # the classifier's raw guess — never overwritten, even on fallback
    routing_confidence: float
    routed_agent: str  # the agent node that actually ran; differs from `intent` only on a confidence-floor fallback
    retrieved_context: list[tuple[str, str]]
    graph_paths: list[dict]
    agent_response: str
    citations: list[str]
    ragas_scores: dict[str, float]  # numeric-only; populated (3 keys) only when ragas_status == "scored"
    ragas_status: str  # "scored" | "skipped_no_context" | "skipped_disabled" | "error" — lets a consumer tell "nothing to score" apart from "scoring turned off" apart from "scoring broke" apart from real numbers
    ragas_detail: str  # provider/scoring error detail when ragas_status == "error"
    low_faithfulness: bool  # split out of ragas_scores since it's not numeric; only meaningful when ragas_status == "scored"
    session_id: str
    memory_context: list[str]
    messages: list[dict[str, Any]]


# Single source of truth for valid intent labels — shared by agents/llm.py
# (validating the classifier's own output) and agents/supervisor.py (routing
# dispatch), so the four-way split isn't duplicated in two places.
INTENTS = ["copilot", "rca", "compliance", "lessons_learned"]
