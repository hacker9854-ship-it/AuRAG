"""Graph-traversal retrieval: closed-world entity extraction from the query
text (reusing ingestion.pipeline's fuzzy matchers — no new matching logic,
no LLM call per query), then traversal to both linked Chunks and structured
records (FailureEvent/WorkOrder/RegulatoryClause/Procedure), synthesized
into passage text on the fly since those records don't have a .text field.
"""
import re

from ingestion.pipeline import load_known_entities, match_equipment, match_person

_PUNCT_RE = re.compile(r"[?.,;:!]+$")


def extract_query_entities(query: str, known_tags: set[str], known_names: set[str]) -> tuple[list[str], list[str]]:
    """Returns (matched_tags, matched_names). Equipment: each whitespace token
    tried as-is. Person: bigrams tried, since seed names are all "First Last"."""
    words = [_PUNCT_RE.sub("", w) for w in query.split()]

    tags = []
    for w in words:
        hit = match_equipment(w, known_tags)
        if hit and hit not in tags:
            tags.append(hit)

    names = []
    for a, b in zip(words, words[1:]):
        hit = match_person(f"{a} {b}", known_names)
        if hit and hit not in names:
            names.append(hit)

    return tags, names


_EQUIPMENT_CYPHER = """
MATCH (e:Equipment {tag_id:$tag})
OPTIONAL MATCH (fe:FailureEvent)-[:OCCURRED_ON]->(e)
OPTIONAL MATCH (wo:WorkOrder)-[:PERFORMED_ON]->(e)
OPTIONAL MATCH (rc:RegulatoryClause)-[:APPLIES_TO]->(e)
OPTIONAL MATCH (proc:Procedure)-[:GOVERNS]->(e)
OPTIONAL MATCH (c:Chunk)-[:MENTIONS]->(e)
RETURN
  collect(DISTINCT {id: fe.id, date: fe.date, symptom: fe.symptom, root_cause: fe.root_cause}) AS failure_events,
  collect(DISTINCT {id: wo.id, date: wo.date, type: wo.type, status: wo.status, description: wo.description}) AS work_orders,
  collect(DISTINCT {id: rc.clause_id, source: rc.source, text: rc.requirement_text}) AS clauses,
  collect(DISTINCT {id: proc.id, title: proc.title, version: proc.version}) AS procedures,
  collect(DISTINCT {id: c.id, text: c.text}) AS chunks
"""

_PERSON_CYPHER = """
MATCH (p:Person {name:$name})
OPTIONAL MATCH (wo:WorkOrder)-[:PERFORMED_BY]->(p)
OPTIONAL MATCH (c:Chunk)-[:MENTIONS]->(p)
RETURN
  collect(DISTINCT {id: wo.id, date: wo.date, type: wo.type, status: wo.status, description: wo.description}) AS work_orders,
  collect(DISTINCT {id: c.id, text: c.text}) AS chunks
"""


def traverse(session, query: str, top_k: int = 5) -> list[tuple[str, str]]:
    """Returns [(key, text), ...] candidate passages, deduped by key."""
    known_tags, known_names = load_known_entities(session)
    tags, names = extract_query_entities(query, known_tags, known_names)

    seen: dict[str, str] = {}

    for tag in tags:
        row = session.run(_EQUIPMENT_CYPHER, tag=tag).single()
        for fe in row["failure_events"]:
            if fe["id"]:
                seen[fe["id"]] = (
                    f"{fe['id']} ({fe['date']}): {fe['symptom']} "
                    f"— root cause: {fe['root_cause']}"
                )
        for wo in row["work_orders"]:
            if wo["id"]:
                seen[wo["id"]] = (
                    f"{wo['id']} ({wo['date']}, {wo['type']}, "
                    f"{wo['status']}): {wo['description']}"
                )
        for rc in row["clauses"]:
            if rc["id"]:
                seen[rc["id"]] = f"{rc['id']} ({rc['source']}): {rc['text']}"
        for proc in row["procedures"]:
            if proc["id"]:
                seen[proc["id"]] = f"{proc['id']} v{proc['version']}: {proc['title']}"
        for c in row["chunks"]:
            if c["id"]:
                seen[c["id"]] = c["text"]

    for name in names:
        row = session.run(_PERSON_CYPHER, name=name).single()
        for wo in row["work_orders"]:
            if wo["id"]:
                seen[wo["id"]] = (
                    f"{wo['id']} ({wo['date']}, {wo['type']}, "
                    f"{wo['status']}): {wo['description']}"
                )
        for c in row["chunks"]:
            if c["id"]:
                seen[c["id"]] = c["text"]

    return list(seen.items())[:top_k] if top_k else list(seen.items())


if __name__ == "__main__":
    import truststore
    truststore.inject_into_ssl()
    from retrieval.index_chunks import get_driver, get_database

    driver, db = get_driver(), get_database()
    with driver.session(database=db) as session:
        results = traverse(session, "Why did P-101 fail in March 2025?")
    assert results, "expected graph-traversal hits for a P-101 query"
    assert any(k.startswith("FE-") for k, _ in results), f"expected a FailureEvent hit, got {[k for k,_ in results]}"
    for key, text in results:
        print(f"{key}: {text[:80]!r}")
