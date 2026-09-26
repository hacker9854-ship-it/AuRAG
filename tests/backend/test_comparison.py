from threading import Event

from backend.app.services.comparison import compare_answers


def test_comparison_keeps_graph_and_plain_contexts_independent():
    def graph_answer(_session, query):
        return {
            "user_query": query,
            "agent_response": "Graph answer",
            "citations": ["FE-001", "PROC-001"],
            "retrieved_context": [
                ("FE-001", "failure evidence"),
                ("PROC-001", "procedure evidence"),
            ],
            "graph_paths": [{"type": "FailureEvent", "id": "FE-001"}],
        }

    def plain_retrieve(query, top_k):
        assert query == "Why did P-101 fail?"
        assert top_k == 5
        return [
            ("FE-001", "failure evidence", 0.91),
            ("CHUNK-9", "similar pump text", 0.83),
        ]

    def plain_answer(query, context):
        assert query == "Why did P-101 fail?"
        assert context[1][0] == "CHUNK-9"
        return {
            "agent_response": "Plain answer",
            "citations": ["CHUNK-9"],
        }

    result = compare_answers(
        session=object(),
        query="Why did P-101 fail?",
        graph_answer_fn=graph_answer,
        plain_retrieve_fn=plain_retrieve,
        plain_answer_fn=plain_answer,
    )

    assert result["graph_rag"]["agent_response"] == "Graph answer"
    assert result["plain_rag"]["agent_response"] == "Plain answer"
    assert result["graph_rag"]["latency_ms"] >= 0
    assert result["plain_rag"]["latency_ms"] >= 0
    assert result["comparison_metrics"] == {
        "shared_sources": ["FE-001"],
        "graph_only_sources": ["PROC-001"],
        "plain_only_sources": ["CHUNK-9"],
        "source_overlap_pct": 33.3,
        "graph_relationship_evidence": 1,
    }


def test_graph_and_plain_paths_execute_concurrently():
    plain_started = Event()
    graph_started = Event()

    def graph_answer(_session, query):
        assert plain_started.wait(timeout=1)
        graph_started.set()
        return {
            "user_query": query,
            "agent_response": "Graph answer",
            "citations": [],
            "retrieved_context": [],
            "graph_paths": [],
        }

    def plain_retrieve(_query, top_k):
        assert top_k == 5
        plain_started.set()
        assert graph_started.wait(timeout=1)
        return []

    result = compare_answers(
        session=object(),
        query="Compare",
        graph_answer_fn=graph_answer,
        plain_retrieve_fn=plain_retrieve,
        plain_answer_fn=lambda _query, _context: {
            "agent_response": "Plain answer",
            "citations": [],
        },
    )

    assert result["graph_rag"]["agent_response"] == "Graph answer"
    assert result["plain_rag"]["agent_response"] == "Plain answer"


def test_comparison_api_rejects_blank_query():
    from fastapi import HTTPException

    from backend.app.api.comparison import ComparisonRequest, comparison

    try:
        comparison(ComparisonRequest(query="   "), session=object())
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail["error"] == "invalid_query"
    else:
        raise AssertionError("blank comparison queries must be rejected")
