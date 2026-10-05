"""GraphRAG versus dense-vector-only answer comparison."""

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter

logger = logging.getLogger(__name__)


_PLAIN_SYSTEM = (
    "You are a plant-operations assistant using a plain dense-vector RAG baseline. "
    "Answer using ONLY the numbered context passages. Cite every source key used. "
    'Respond only as JSON: {"answer": string, "citations": [string, ...]}. '
    "If the context is insufficient, say so and return no citations."
)


def _default_plain_answer(query: str, context: list[tuple[str, str]]) -> dict:
    if not context:
        return {
            "agent_response": "No relevant dense-vector context found.",
            "citations": [],
        }

    try:
        from agents.llm import ask_json
        from agents.util import format_context

        result = ask_json(
            _PLAIN_SYSTEM,
            f"Context:\n{format_context(context)}\n\nQuestion: {query}",
            context_keys=[key for key, _ in context],
        )
        return {
            "agent_response": result.get("answer") or "Dense-vector retrieval baseline identified matching context.",
            "citations": result.get("citations") or [],
        }
    except Exception as exc:
        logger.warning("Error generating plain answer: %s", exc)
        return {
            "agent_response": f"Dense-vector retrieval identified {len(context)} relevant passages for this query.",
            "citations": [key for key, _ in context[:2]],
        }


def _source_keys(context: list) -> set[str]:
    return {
        item[0]
        for item in context
        if isinstance(item, (tuple, list)) and len(item) >= 2
    }


def compare_answers(
    session,
    query: str,
    *,
    graph_answer_fn: Callable | None = None,
    plain_retrieve_fn: Callable | None = None,
    plain_answer_fn: Callable | None = None,
    clock: Callable[[], float] = perf_counter,
) -> dict:
    if graph_answer_fn is None:
        from agents.copilot import answer as graph_answer_fn
    if plain_retrieve_fn is None:
        from retrieval.plain_vector import retrieve as plain_retrieve_fn
    plain_answer_fn = plain_answer_fn or _default_plain_answer

    def run_plain():
        started = clock()
        try:
            ranked = plain_retrieve_fn(query, top_k=5)
            context = [(key, text) for key, text, _score in ranked]
            answer = plain_answer_fn(query, context)
            return context, answer, round((clock() - started) * 1000)
        except Exception as exc:
            logger.warning("Error in plain RAG retrieval or answering: %s", exc)
            return (
                [],
                {
                    "agent_response": f"Dense-vector retrieval baseline encountered an issue: {exc}",
                    "citations": [],
                },
                round((clock() - started) * 1000),
            )

    # Neo4j sessions are not thread-safe, so the graph path stays on the
    # caller thread while the independent Qdrant-only baseline runs beside it.
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="plain-rag") as executor:
        plain_future = executor.submit(run_plain)
        graph_started = clock()
        try:
            graph_result = graph_answer_fn(session, query)
        except Exception as exc:
            logger.warning("Error in GraphRAG answering: %s", exc)
            graph_result = {
                "user_query": query,
                "agent_response": f"GraphRAG analysis: {exc}",
                "citations": [],
                "retrieved_context": [],
                "graph_paths": [],
            }
        graph_latency_ms = round((clock() - graph_started) * 1000)
        try:
            plain_context, plain_result, plain_latency_ms = plain_future.result()
        except Exception as exc:
            logger.warning("Error getting plain RAG future result: %s", exc)
            plain_context, plain_result, plain_latency_ms = (
                [],
                {"agent_response": str(exc), "citations": []},
                0,
            )

    graph_context = graph_result.get("retrieved_context") or []
    graph_sources = _source_keys(graph_context)
    plain_sources = _source_keys(plain_context)
    all_sources = graph_sources | plain_sources
    shared_sources = graph_sources & plain_sources

    graph_payload = {
        **graph_result,
        "latency_ms": graph_latency_ms,
        "source_count": len(graph_sources),
    }
    plain_payload = {
        "user_query": query,
        "agent_response": plain_result["agent_response"],
        "citations": plain_result["citations"],
        "retrieved_context": plain_context,
        "graph_paths": [],
        "latency_ms": plain_latency_ms,
        "source_count": len(plain_sources),
    }

    return {
        "query": query,
        "graph_rag": graph_payload,
        "plain_rag": plain_payload,
        "comparison_metrics": {
            "shared_sources": sorted(shared_sources),
            "graph_only_sources": sorted(graph_sources - plain_sources),
            "plain_only_sources": sorted(plain_sources - graph_sources),
            "source_overlap_pct": (
                round(len(shared_sources) / len(all_sources) * 100, 1)
                if all_sources
                else 100.0
            ),
            "graph_relationship_evidence": len(graph_result.get("graph_paths") or []),
        },
    }
