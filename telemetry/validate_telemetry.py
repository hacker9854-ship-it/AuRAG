"""Deterministic telemetry precision/recall acceptance benchmark."""

import truststore

truststore.inject_into_ssl()

from retrieval.index_chunks import get_database, get_driver
from telemetry.draft import _CONFIDENCE_FLOOR
from telemetry.generator import generate_reading
from telemetry.pattern_match import match_reading

_MIN_PRECISION = 0.95
_MIN_RECALL = 0.95


def _failure_events(session) -> list[tuple[str, str]]:
    return [
        (row["id"], row["tag"])
        for row in session.run(
            """
            MATCH (f:FailureEvent)-[:OCCURRED_ON]->(e:Equipment)
            WHERE f.signature_json IS NOT NULL
            RETURN f.id AS id, e.tag_id AS tag
            ORDER BY f.id
            """
        ).data()
    ]


def _prediction(matches: list[dict]) -> str | None:
    if not matches or matches[0]["similarity"] < _CONFIDENCE_FLOOR:
        return None
    return matches[0]["failure_event_id"]


def benchmark(session) -> dict:
    events = _failure_events(session)
    equipment_tags = sorted({tag for _, tag in events})
    true_positive = false_positive = false_negative = true_negative = 0
    confusion: dict[str, dict[str, int]] = {}

    for event_id, tag in events:
        reading = generate_reading(
            session,
            tag,
            drift_toward=event_id,
            drift_pct=1.0,
            noise=False,
        )
        predicted = _prediction(match_reading(session, tag, reading))
        confusion.setdefault(event_id, {})
        confusion[event_id][predicted or "none"] = (
            confusion[event_id].get(predicted or "none", 0) + 1
        )
        if predicted == event_id:
            true_positive += 1
        else:
            false_negative += 1
            if predicted is not None:
                false_positive += 1

    for tag in equipment_tags:
        for drift_pct in (0.0, 0.5, 0.75):
            reading = generate_reading(
                session,
                tag,
                drift_pct=drift_pct,
                noise=False,
            )
            predicted = _prediction(match_reading(session, tag, reading))
            if predicted is None:
                true_negative += 1
            else:
                false_positive += 1

    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 1.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else 1.0
    )
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
        "precision": precision,
        "recall": recall,
        "confusion": confusion,
    }


def main() -> None:
    driver, db = get_driver(), get_database()
    try:
        with driver.session(database=db) as session:
            result = benchmark(session)
    finally:
        driver.close()

    print(
        "Telemetry benchmark: "
        f"TP={result['true_positive']} FP={result['false_positive']} "
        f"FN={result['false_negative']} TN={result['true_negative']} "
        f"precision={result['precision']:.3f} recall={result['recall']:.3f}"
    )
    for expected, predictions in result["confusion"].items():
        print(f"  {expected}: {predictions}")

    assert result["precision"] >= _MIN_PRECISION, result
    assert result["recall"] >= _MIN_RECALL, result
    print("OK: telemetry precision and recall thresholds passed")


if __name__ == "__main__":
    main()
