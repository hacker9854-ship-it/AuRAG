"""Turns a pattern-match result into (1) a proactive warning and (2) a
draft work order, per PRD Section 8b steps 1-2. Step 3 ("let the user
accept/edit/reject") is a persistence + UI concern — out of scope here, same
as every prior phase's "backend logic only" boundary; nothing here writes to
Neo4j."""
from retrieval.graph_traversal import traverse

# ponytail: fixed threshold, not tuned against a large query set — this
# phase's validate_telemetry.py sweep IS the tuning pass PRD Section 14 asks
# for; revisit if it shows the floor sitting in a bad spot.
_CONFIDENCE_FLOOR = 0.8


def build_warning(equipment_tag: str, matches: list[dict]) -> dict | None:
    """None if nothing crosses the confidence floor — no proactive push,
    directly avoiding PRD Section 14's named false-positive risk."""
    if not matches or matches[0]["similarity"] < _CONFIDENCE_FLOOR:
        return None
    top = matches[0]
    return {
        "equipment": equipment_tag,
        "matched_failure_event": top["failure_event_id"],
        "similarity": top["similarity"],
        "symptom": top["symptom"],
    }


def _recommended_action(session, equipment_tag: str) -> str:
    """Governing Procedure title for this equipment, via the existing
    entity-anchored traversal (reused, not a new Cypher query) — traverse()
    treats its query string as free text, so passing the tag itself is
    enough for extract_query_entities' whitespace-token matcher to find it."""
    for key, text in traverse(session, equipment_tag, top_k=None):
        if key.startswith("PROC-"):
            return text
    return "No governing procedure found — manual review required."


def draft_work_order(session, equipment_tag: str, top_match: dict) -> dict:
    """Plain dict shaped like the existing WorkOrder seed records. status
    'Draft' is a new value distinct from Open/Closed/Overdue, meaning
    system-proposed and not yet actioned. Not persisted to Neo4j — that only
    happens after an explicit user accept, which is Phase 8 territory."""
    return {
        "type": "Corrective",
        "status": "Draft",
        "equipment": equipment_tag,
        "description": f"Auto-drafted from {top_match['failure_event_id']} pattern match: {top_match['root_cause']}",
        "recommended_action": _recommended_action(session, equipment_tag),
    }


if __name__ == "__main__":
    import truststore

    truststore.inject_into_ssl()
    from retrieval.index_chunks import get_database, get_driver

    from telemetry.generator import generate_reading
    from telemetry.pattern_match import match_reading

    driver, db = get_driver(), get_database()
    with driver.session(database=db) as session:
        reading = generate_reading(session, "P-101", drift_toward="FE-001", drift_pct=1.0, noise=False)
        matches = match_reading(session, "P-101", reading)
        warning = build_warning("P-101", matches)
        work_order = draft_work_order(session, "P-101", matches[0])
    driver.close()

    assert warning is not None and warning["matched_failure_event"] == "FE-001", warning
    assert work_order["status"] == "Draft"
    assert work_order["recommended_action"], "expected a non-empty recommended_action"
    print("warning:", warning)
    print("work_order:", work_order)
    print("OK: telemetry.draft self-check passed")
