"""Synthetic telemetry generator per PRD Section 8b: produces a numeric
feature-vector reading for a piece of equipment, either "healthy" (nominal ±
small noise) or drifted toward a known FailureEvent's stored signature.
`drift_pct` is the literal backend primitive for the PRD's "telemetry slider
the presenter can move live" — 0.0 = nominal, 1.0 = the exact failure
signature, everything between is a proportional partial match.

Reads FailureEvent.signature_json from Neo4j (the single source of truth,
seeded by infra/neo4j/seed/07_telemetry_signatures.cypher) rather than
duplicating those values in Python — only the "healthy" baseline is Python-
only, since it's a synthesis assumption with no home in the graph."""
import json
import random

# ponytail: nominal (healthy) baseline per dimension — synthesis assumption,
# not plant data, so it lives here rather than in Neo4j. set_pressure_pct is
# the one dimension where failure means a LOWER value than nominal.
NOMINAL = {
    "vibration_mm_s": 2.0,
    "bearing_temp_c": 55.0,
    "discharge_temp_c": 120.0,
    "outlet_temp_deviation_c": 1.0,
    "set_pressure_pct": 100.0,
    "differential_pressure_kpa": 18.0,
    "seal_leak_rate_ml_min": 0.5,
}

# Display metadata per dimension for the telemetry metric grid (label + unit).
# nominal is derived from NOMINAL above rather than duplicated — see meta_for().
DIMENSION_LABELS = {
    "vibration_mm_s": ("Vibration", "mm/s"),
    "bearing_temp_c": ("Bearing temperature", "°C"),
    "discharge_temp_c": ("Discharge temperature", "°C"),
    "outlet_temp_deviation_c": ("Outlet temperature delta", "°C"),
    "set_pressure_pct": ("Set pressure", "%"),
    "differential_pressure_kpa": ("Differential pressure", "kPa"),
    "seal_leak_rate_ml_min": ("Seal leak rate", "mL/min"),
}


def meta_for(dimensions) -> dict:
    """{dim: {"label", "unit", "nominal"}} for each given dimension key.
    Lets the frontend render a reading's known fields cleanly without
    hardcoding units/labels client-side."""
    meta = {}
    for dim in dimensions:
        if dim in DIMENSION_LABELS:
            label, unit = DIMENSION_LABELS[dim]
            meta[dim] = {"label": label, "unit": unit, "nominal": NOMINAL[dim]}
    return meta

_NOISE_FRACTION = 0.02  # 2% of the nominal->failure span per dimension


def _equipment_signatures(session, equipment_tag: str) -> list[tuple[str, dict]]:
    """[(failure_event_id, {dim: failure_value}), ...] for this equipment."""
    rows = session.run(
        "MATCH (f:FailureEvent)-[:OCCURRED_ON]->(e:Equipment {tag_id: $tag}) "
        "RETURN f.id AS id, f.signature_json AS sig",
        tag=equipment_tag,
    ).data()
    return [(row["id"], json.loads(row["sig"])) for row in rows if row["sig"]]


def generate_reading(
    session,
    equipment_tag: str,
    drift_toward: str | None = None,
    drift_pct: float = 0.0,
    noise: bool = True,
    rng: random.Random | None = None,
) -> dict:
    """Returns {"equipment": equipment_tag, <dim>: value, ...}. Dimensions are
    whichever this equipment's own FailureEvent history uses — no dimension
    is invented for equipment with no failure history (returns just
    {"equipment": ...} in that case)."""
    signatures = _equipment_signatures(session, equipment_tag)
    if not signatures:
        return {"equipment": equipment_tag}

    if drift_toward is not None:
        matching = [sig for fe_id, sig in signatures if fe_id == drift_toward]
        if not matching:
            raise ValueError(f"{drift_toward} is not a FailureEvent for {equipment_tag}")
        target = matching[0]
    else:
        # No specific target: use the first known signature's dimensions for
        # a healthy reading. Explicit drift tests should always name a target
        # when equipment has multiple historical failure modes.
        target = signatures[0][1]

    rng = rng or random
    reading = {"equipment": equipment_tag}
    for dim, failure_val in target.items():
        nominal_val = NOMINAL[dim]
        value = nominal_val + (failure_val - nominal_val) * drift_pct
        if noise:
            span = abs(nominal_val - failure_val)
            value += rng.gauss(0, span * _NOISE_FRACTION)
        reading[dim] = value
    return reading


if __name__ == "__main__":
    import truststore

    truststore.inject_into_ssl()
    from retrieval.index_chunks import get_database, get_driver

    driver, db = get_driver(), get_database()
    with driver.session(database=db) as session:
        healthy = generate_reading(session, "P-101", noise=False)
        failure = generate_reading(session, "P-101", drift_toward="FE-001", drift_pct=1.0, noise=False)
    driver.close()

    assert healthy == {"equipment": "P-101", "vibration_mm_s": 2.0, "bearing_temp_c": 55.0}, healthy
    assert failure == {"equipment": "P-101", "vibration_mm_s": 7.5, "bearing_temp_c": 87.0}, failure
    assert meta_for(["vibration_mm_s", "equipment"]) == {
        "vibration_mm_s": {"label": "Vibration", "unit": "mm/s", "nominal": 2.0}
    }, "meta_for should map known dims and skip unknown keys"
    print("healthy:", healthy)
    print("failure (drift_pct=1.0):", failure)
    print("OK: telemetry.generator self-check passed")
