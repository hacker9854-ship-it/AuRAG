"""Matches a live telemetry reading against stored FailureEvent signatures,
per PRD Section 8b: similarity-scored, not fixed per-field thresholds, so
"close but not exact" patterns still surface with a proportional score.

Similarity formula, corrected from an earlier draft that normalized each
dimension's distance against the raw failure-signature value
(`|reading-signature|/signature`). That breaks for downward-failure
dimensions: set_pressure_pct healthy=100/failure=90 gives
1 - |100-90|/90 = 0.889, wrongly crossing a 0.8 confidence floor on a fully
healthy reading. Fixed: normalize against the nominal->failure span instead,
so a dimension's distance is measured relative to how far THAT dimension's
own failure gap actually is — 0 similarity at nominal, 1.0 at the exact
failure value, regardless of which direction failure moves in."""
import json

from telemetry.generator import NOMINAL


def _dimension_similarity(reading_val: float, failure_val: float, nominal_val: float) -> float:
    span = abs(nominal_val - failure_val)
    if span == 0:
        return 1.0 if reading_val == failure_val else 0.0
    distance = abs(reading_val - failure_val) / span
    return 1.0 - min(distance, 1.0)


def match_reading(session, equipment_tag: str, reading: dict) -> list[dict]:
    """Returns matches sorted by similarity descending, each:
    {"failure_event_id":, "similarity":, "symptom":, "root_cause":}.

    Strict dimension-presence rule: a FailureEvent is only scored if EVERY
    dimension in its signature is present in the reading. A reading missing
    one of a signature's expected dimensions is not a partial match on the
    remaining ones — that would be an overconfident guess, not a real
    similarity score."""
    rows = session.run(
        "MATCH (f:FailureEvent)-[:OCCURRED_ON]->(e:Equipment {tag_id: $tag}) "
        "RETURN f.id AS id, f.signature_json AS sig, f.symptom AS symptom, f.root_cause AS root_cause",
        tag=equipment_tag,
    ).data()

    matches = []
    for row in rows:
        if not row["sig"]:
            continue
        signature = json.loads(row["sig"])
        if not all(dim in reading for dim in signature):
            continue

        similarities = [
            _dimension_similarity(reading[dim], failure_val, NOMINAL[dim])
            for dim, failure_val in signature.items()
        ]
        matches.append(
            {
                "failure_event_id": row["id"],
                "similarity": sum(similarities) / len(similarities),
                "symptom": row["symptom"],
                "root_cause": row["root_cause"],
            }
        )

    return sorted(matches, key=lambda m: m["similarity"], reverse=True)


if __name__ == "__main__":
    import truststore

    truststore.inject_into_ssl()
    from retrieval.index_chunks import get_database, get_driver

    from telemetry.generator import generate_reading

    driver, db = get_driver(), get_database()
    with driver.session(database=db) as session:
        failure_reading = generate_reading(session, "P-101", drift_toward="FE-001", drift_pct=1.0, noise=False)
        failure_matches = match_reading(session, "P-101", failure_reading)

        healthy_reading = generate_reading(session, "P-101", noise=False)
        healthy_matches = match_reading(session, "P-101", healthy_reading)
    driver.close()

    assert failure_matches[0]["failure_event_id"] == "FE-001", failure_matches
    assert abs(failure_matches[0]["similarity"] - 1.0) < 1e-6, failure_matches
    assert abs(healthy_matches[0]["similarity"] - 0.0) < 1e-6, healthy_matches
    print("failure reading matches:", failure_matches)
    print("healthy reading matches:", healthy_matches)
    print("OK: telemetry.pattern_match self-check passed")
