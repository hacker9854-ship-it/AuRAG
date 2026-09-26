"""Copilot sub-agent: general Q&A with citations, grounded in the fused
hybrid retrieval layer (Neo4j vector + Qdrant dense + BM25 + graph traversal,
cross-encoder reranked) per PRD Section 8 item 3 — not plain vector RAG."""
from agents.llm import ask_json
from agents.util import format_context, format_memory_context, graph_paths
from retrieval.hybrid import retrieve

_SYSTEM = (
    'You are a plant-operations Copilot. Answer the question using ONLY the '
    "numbered context passages given, each tagged with its source key like "
    '[FE-001]. Cite every key you actually relied on. State findings in your '
    "own words — don't copy sentences directly from retrieved context. "
    "When the question asks what a requirement or standard requires, "
    "prioritize the matching RegulatoryClause passage and distinguish that "
    "requirement from incident history or a work-order schedule. "
    'Respond only as JSON: {"answer": string, "citations": [string, ...]}. '
    "If the context does not answer the question, say so in `answer` and "
    "return an empty citations list."
)


def answer(session, query: str, memory_context: list[str] | None = None) -> dict:
    context = retrieve(session, query, top_k=5)
    items = [(key, text) for key, text, _ in context]

    if not items:
        return {"user_query": query, "agent_response": "No relevant context found.",
                "citations": [], "retrieved_context": [], "graph_paths": []}

    memory_note = format_memory_context(memory_context or [])
    user_prompt = f"Context:\n{format_context(items)}"
    if memory_note:
        user_prompt += (
            "\n\nNon-authoritative memory from earlier sessions "
            "(do not cite it or treat it as plant evidence):\n"
            f"{memory_note}"
        )
    user_prompt += f"\n\nQuestion: {query}"
    result = ask_json(_SYSTEM, user_prompt, context_keys=[k for k, _ in items])

    return {
        "user_query": query,
        "agent_response": result["answer"],
        "citations": result["citations"],
        "retrieved_context": items,
        "graph_paths": graph_paths(result["citations"]),
    }


if __name__ == "__main__":
    import truststore
    truststore.inject_into_ssl()
    from retrieval.index_chunks import get_driver, get_database

    driver, db = get_driver(), get_database()
    with driver.session(database=db) as session:
        result = answer(session, "Why did P-101 fail in March 2025?")
    driver.close()

    assert result["citations"], "expected non-empty citations"
    print(result["agent_response"])
    print("citations:", result["citations"])
    print("OK: agents.copilot self-check passed")
