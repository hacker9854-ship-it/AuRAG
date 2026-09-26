"""Supervisor: a LangGraph StateGraph that classifies query intent then routes
to the matching sub-agent, per PRD Section 5 ("Supervisor + specialized
sub-agents pattern... The Supervisor's only job is correct routing — it does
not do the domain reasoning itself"). Low-confidence classifications fall back
to Copilot (general hybrid retrieval), per PRD Section 14's named mitigation
for ambiguous/mixed-intent queries — Copilot is both a real intent and the
fallback target, so no separate fallback node is needed."""
from langgraph.graph import END, StateGraph

from agents import compliance, copilot, lessons_learned, rca
from agents.llm import classify_intent
from agents.state import INTENTS, AgentState

# ponytail: fixed threshold, not tuned against a large query set — revisit if
# agents.validate_supervisor shows real misroutes worth tuning against.
_CONFIDENCE_FLOOR = 0.6

_ANSWER_FNS = {
    "copilot": copilot.answer,
    "rca": rca.answer,
    "compliance": compliance.answer,
    "lessons_learned": lessons_learned.answer,
}


def _route(state: AgentState) -> str:
    if state["intent"] in INTENTS and state["routing_confidence"] >= _CONFIDENCE_FLOOR:
        return state["intent"]
    return "copilot"


def build_graph(session, score: bool = True):
    def supervisor_node(state: AgentState) -> dict:
        result = classify_intent(state["user_query"])
        return {"intent": result["intent"], "routing_confidence": result["confidence"]}

    def make_agent_node(name, answer_fn):
        def node(state: AgentState) -> dict:
            # Stamp `routed_agent` with the agent that actually ran — distinct
            # from `intent`, which stays the classifier's raw guess untouched.
            # On a confidence-floor fallback the two diverge (e.g. intent=rca,
            # routed_agent=copilot); collapsing them into one field would lose
            # visibility into either "what the classifier guessed" or "what
            # actually ran" — both matter for debugging future misroutes.
            result = answer_fn(
                session,
                state["user_query"],
                memory_context=state.get("memory_context") or [],
            )
            result["routed_agent"] = name
            return result
        return node

    def score_node(state: AgentState) -> dict:
        # Defensive: don't assume every agent's retrieved_context stays a
        # clean list forever.
        context = state.get("retrieved_context") or []
        if not context:
            # RCA/Compliance's "no entity matched" short-circuit returns a
            # canned message with no LLM call at all — scoring faithfulness
            # of a static string against empty context is degenerate and
            # would only burn a Groq round-trip for no signal.
            return {"ragas_scores": {}, "ragas_status": "skipped_no_context", "low_faithfulness": False}

        try:
            # Lazy import: ragas/langchain-groq stay optional to the core
            # routing path — a missing/broken eval install must not break
            # answering, only scoring.
            from evaluation.score import score_answer

            result = score_answer(state["user_query"], state["agent_response"], context)
            return {
                "ragas_scores": {k: result[k] for k in ("faithfulness", "context_precision", "answer_relevancy")},
                "ragas_status": "scored",
                "low_faithfulness": result["low_faithfulness"],
            }
        except Exception as exc:
            # Fail open: the answer was already produced by the upstream
            # agent node and must still be returned. Scoring is additive
            # metadata, never a gate on whether an answer comes back.
            print(f"[evaluation.score] scoring failed, answer still returned: {exc}")
            return {
                "ragas_scores": {},
                "ragas_status": "error",
                "ragas_detail": str(exc),
                "low_faithfulness": False,
            }

    graph = StateGraph(AgentState)
    graph.add_node("supervisor", supervisor_node)
    for name, fn in _ANSWER_FNS.items():
        graph.add_node(name, make_agent_node(name, fn))

    graph.set_entry_point("supervisor")
    graph.add_conditional_edges("supervisor", _route, {name: name for name in INTENTS})

    if score:
        graph.add_node("score", score_node)
        for name in INTENTS:
            graph.add_edge(name, "score")
        graph.add_edge("score", END)
    else:
        # Validation-only path (agents.validate_supervisor): routing/citation
        # checks don't need RAGAS, so skip the judge-LLM-heavy score node
        # entirely rather than running it and discarding the result — that's
        # the actual quota burn this flag exists to avoid.
        for name in INTENTS:
            graph.add_edge(name, END)

    return graph.compile()


def answer(
    session,
    query: str,
    score: bool = True,
    memory_context: list[str] | None = None,
    session_id: str | None = None,
) -> dict:
    graph = build_graph(session, score=score)
    result = graph.invoke(
        {
            "user_query": query,
            "memory_context": memory_context or [],
            "session_id": session_id or "",
        }
    )
    if not score:
        result.setdefault("ragas_scores", {})
        result.setdefault("ragas_status", "skipped_disabled")
        result.setdefault("low_faithfulness", False)
    return result


if __name__ == "__main__":
    import truststore
    truststore.inject_into_ssl()
    from retrieval.index_chunks import get_driver, get_database

    driver, db = get_driver(), get_database()
    with driver.session(database=db) as session:
        result = answer(session, "What caused the P-101 failure?")
        unscored = answer(session, "What caused the P-101 failure?", score=False)
    driver.close()

    assert result["routed_agent"] in INTENTS, f"unexpected routed_agent: {result['routed_agent']}"
    assert result["agent_response"], "expected a non-empty answer"
    assert result["ragas_status"] in ("scored", "skipped_no_context", "error"), f"unexpected ragas_status: {result['ragas_status']}"
    if result["ragas_status"] == "scored":
        assert set(result["ragas_scores"]) == {"faithfulness", "context_precision", "answer_relevancy"}, result["ragas_scores"]

    assert unscored["ragas_status"] == "skipped_disabled", f"unexpected ragas_status: {unscored['ragas_status']}"
    assert unscored["ragas_scores"] == {}, unscored["ragas_scores"]
    assert unscored["low_faithfulness"] is False, unscored["low_faithfulness"]
    assert unscored["agent_response"], "expected a non-empty answer even with scoring disabled"

    print(
        f"classified as: {result['intent']} (confidence={result['routing_confidence']:.2f}) "
        f"-> routed to: {result['routed_agent']}"
    )
    print(result["agent_response"])
    print(f"ragas_status={result['ragas_status']} scores={result['ragas_scores']} low_faithfulness={result['low_faithfulness']}")
    print("OK: agents.supervisor self-check passed")
