"""Maps a retrieval/citation key to its Neo4j node type by id-prefix
convention (confirmed against infra/neo4j/seed/*.cypher), so agents can build
a typed `graph_paths` list from a flat `citations` list of ids for the
answer-trail visualization differentiator (PRD Section 9)."""

_PREFIXES = [
    ("FE-", "FailureEvent"),
    ("WO-", "WorkOrder"),
    ("PROC-", "Procedure"),
    ("FACT", "RegulatoryClause"),
    ("OISD-", "RegulatoryClause"),
    ("DOC-", "Chunk"),
]


def classify_key(key: str) -> str:
    for prefix, node_type in _PREFIXES:
        if key.startswith(prefix):
            return node_type
    return "Unknown"


def graph_paths(citations: list[str]) -> list[dict]:
    return [{"type": classify_key(c), "id": c} for c in citations]


def format_context(items: list[tuple[str, str]]) -> str:
    """(key, text) pairs -> numbered context block for an LLM prompt."""
    return "\n".join(f"[{key}] {text}" for key, text in items)


def format_memory_context(memories: list[str]) -> str:
    """Render optional cross-session memory as non-citable prompt context."""
    if not memories:
        return ""
    return "\n".join(f"- {memory}" for memory in memories)


if __name__ == "__main__":
    assert classify_key("FE-001") == "FailureEvent"
    assert classify_key("WO-1002") == "WorkOrder"
    assert classify_key("PROC-001") == "Procedure"
    assert classify_key("OISD-STD-132-10.2ii") == "RegulatoryClause"
    assert classify_key("FACT1948-4-1") == "RegulatoryClause"
    assert classify_key("DOC-LOG-001-C002") == "Chunk"
    assert classify_key("P-101") == "Unknown"
    assert format_context([("FE-001", "bearing wear")]) == "[FE-001] bearing wear"
    print("OK: classify_key self-check passed")
