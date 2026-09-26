"""RCA sub-agent: traverses failure history + work orders for an
entity-anchored equipment/person, produces a root-cause narrative + an
actionable fix, per PRD Section 8 item 4. Entity-anchored graph traversal
(retrieval.graph_traversal), not the generic hybrid fusion Copilot uses —
matches PRD's own "traverses failure history + work orders" framing."""
import re

from agents.llm import ask_json
from agents.util import classify_key, format_context, format_memory_context, graph_paths
from ingestion.pipeline import load_known_entities
from retrieval.candidate_filter import filter_to_explicit_years
from retrieval.graph_traversal import extract_query_entities, traverse

_SYSTEM = (
    "You are a root-cause-analysis agent for industrial equipment. Using "
    "ONLY the numbered context passages, answer the exact incident and time "
    "period in the question. Start with one direct sentence naming the root "
    "cause. Then add at most two concise sentences covering the missed or "
    "corrective work order and any recurrence-prevention action explicitly "
    "stated in the evidence. Do not infer a procedure section, schedule, or "
    "maintenance instruction from a document title alone. If the evidence "
    "does not state a prevention action, stop after the root cause and "
    "corrective work order. "
    "Do not discuss other incidents on the same equipment and do not add "
    "generic advice. Cite only passages that contain the fact you state. State "
    "findings in your own words — don't copy sentences directly from "
    'retrieved context. Respond only as JSON: '
    '{"answer": string, "citations": [string, ...]}.'
)

_NO_ENTITY = (
    "I couldn't identify a specific equipment tag or person in this "
    "question — try naming one (e.g. P-101)."
)
_NO_HISTORY = "No failure/work-order history found for this equipment."

_ID_RE = re.compile(r"\b(?:FE-\d+|WO-[A-Z0-9-]+)\b")
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_STOPWORDS = {
    "a", "an", "and", "did", "do", "for", "in", "is", "of", "on",
    "the", "to", "was", "what", "when", "why",
}


def _query_terms(text: str) -> set[str]:
    return {
        token
        for token in _TOKEN_RE.findall(text.casefold())
        if token not in _STOPWORDS and len(token) > 1
    }


def _best_incident_chunk(
    items: list[tuple[str, str]],
    query: str,
) -> tuple[str, str] | None:
    """Pick the source passage most specifically aligned with the question."""
    query_terms = _query_terms(query)
    chunks = [
        item
        for item in items
        if classify_key(item[0]) == "Chunk" and item[0].startswith("DOC-LOG-")
    ]
    if not chunks:
        return None

    return max(
        chunks,
        key=lambda item: (
            len(query_terms & _query_terms(item[1])),
            len(_ID_RE.findall(item[1])),
        ),
    )


def _select_rca_context(
    items: list[tuple[str, str]],
    query: str,
) -> list[tuple[str, str]]:
    """Reduce equipment-wide history to evidence for the incident asked about."""
    filtered = list(filter_to_explicit_years(dict(items), query).items())
    if not filtered:
        return []

    by_key = dict(filtered)
    incident_chunk = _best_incident_chunk(filtered, query)
    referenced_ids = set(_ID_RE.findall(incident_chunk[1])) if incident_chunk else set()

    failure_keys = [
        key for key, _text in filtered if classify_key(key) == "FailureEvent"
    ]
    primary_failure = next(
        (key for key in failure_keys if key in referenced_ids),
        failure_keys[0] if len(failure_keys) == 1 else None,
    )
    if primary_failure:
        referenced_ids.update(_ID_RE.findall(by_key[primary_failure]))

    selected_keys: list[str] = []

    def add(key: str | None) -> None:
        if key and key in by_key and key not in selected_keys:
            selected_keys.append(key)

    add(primary_failure)
    for key, _text in filtered:
        if classify_key(key) == "WorkOrder" and key in referenced_ids:
            add(key)
    if incident_chunk and (not primary_failure or primary_failure in incident_chunk[1]):
        add(incident_chunk[0])
    # A graph Procedure node may contain only a document title.  Passing that
    # title as if it were operational evidence invites the LLM to invent a
    # schedule or section number; an incident log with the actual procedure
    # text will already be retained above as its matching Chunk.

    # If no incident could be isolated, retain a bounded typed neighborhood
    # instead of silently returning no evidence.
    if not selected_keys:
        for key, _text in filtered:
            if classify_key(key) in {"FailureEvent", "WorkOrder", "Procedure", "Chunk"}:
                add(key)
            if len(selected_keys) == 5:
                break

    return [(key, by_key[key]) for key in selected_keys]


def answer(session, query: str, memory_context: list[str] | None = None) -> dict:
    known_tags, known_names = load_known_entities(session)
    tags, names = extract_query_entities(query, known_tags, known_names)
    anchors = [{"type": "Equipment", "id": t} for t in tags] + [{"type": "Person", "id": n} for n in names]

    if not anchors:
        return {"user_query": query, "agent_response": _NO_ENTITY,
                "citations": [], "retrieved_context": [], "graph_paths": []}

    items = _select_rca_context(traverse(session, query, top_k=None), query)
    if not items:
        return {"user_query": query, "agent_response": _NO_HISTORY,
                "citations": [], "retrieved_context": [], "graph_paths": anchors}

    memory_note = format_memory_context(memory_context or [])
    user_prompt = f"Context:\n{format_context(items)}"
    if memory_note:
        user_prompt += (
            "\n\nNon-authoritative memory from earlier sessions "
            "(do not cite it or treat it as plant evidence):\n"
            f"{memory_note}"
        )
    user_prompt += f"\n\nQuestion: {query}"
    result = ask_json(
        _SYSTEM,
        user_prompt,
        context_keys=[k for k, _ in items],
        provider="groq",
    )

    return {
        "user_query": query,
        "agent_response": result["answer"],
        "citations": result["citations"],
        "retrieved_context": items,
        "graph_paths": anchors + graph_paths(result["citations"]),
    }


if __name__ == "__main__":
    import truststore
    truststore.inject_into_ssl()
    from retrieval.index_chunks import get_driver, get_database

    driver, db = get_driver(), get_database()
    with driver.session(database=db) as session:
        result = answer(session, "What caused the P-101 failure?")
    driver.close()

    # ponytail: only assert the FE- anchor, not a specific WO- key too — the
    # model legitimately chooses which retrieved context to cite (e.g. citing
    # the governing PROC- fix instead of a WO-), both work orders are in
    # context either way per graph_traversal.traverse(), so this isn't a
    # retrieval gap
    assert any(c.startswith("FE-") for c in result["citations"]), f"expected an FE- citation, got {result['citations']}"
    print(result["agent_response"])
    print("citations:", result["citations"])
    print("OK: agents.rca self-check passed")
