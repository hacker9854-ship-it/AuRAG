"""Knowledge-retirement risk queries and deterministic scoring."""

from typing import Any


_RISK_QUERY = """
MATCH (p:Person)
WHERE p.years_to_retirement <= $horizon
OPTIONAL MATCH (w:WorkOrder)-[:PERFORMED_BY]->(p)
OPTIONAL MATCH (w)-[:PERFORMED_ON]->(e:Equipment)
OPTIONAL MATCH (f:FailureEvent)-[:OCCURRED_ON]->(e)
OPTIONAL MATCH (f)-[:DOCUMENTED_IN]->(fd:Document)
OPTIONAL MATCH (pd:Document)-[:CONTAINS]->(:Chunk)-[:MENTIONS]->(p)
WITH p,
     collect(DISTINCT w.id) AS work_orders,
     collect(DISTINCT e.tag_id) AS equipment,
     collect(DISTINCT CASE WHEN toLower(coalesce(e.criticality, '')) IN
       ['critical', 'high'] THEN e.tag_id END) AS critical_equipment,
     collect(DISTINCT f.id) AS failure_events,
     collect(DISTINCT fd.id) + collect(DISTINCT pd.id) AS document_candidates
UNWIND CASE WHEN equipment = [] THEN [null] ELSE equipment END AS equipment_tag
OPTIONAL MATCH (other:Person)<-[:PERFORMED_BY]-(:WorkOrder)-[:PERFORMED_ON]->
  (:Equipment {tag_id: equipment_tag})
WHERE other.person_id <> p.person_id AND other.years_to_retirement > $horizon
WITH p, work_orders, equipment, critical_equipment, failure_events,
     [d IN document_candidates WHERE d IS NOT NULL] AS documents,
     equipment_tag, count(other) AS successor_count
WITH p, work_orders, equipment, critical_equipment, failure_events, documents,
     collect(CASE WHEN equipment_tag IS NOT NULL AND successor_count = 0
       THEN equipment_tag END) AS uncovered_candidates
RETURN p.person_id AS person_id,
       p.name AS name,
       p.role AS role,
       p.department AS department,
       p.years_to_retirement AS years_to_retirement,
       work_orders,
       equipment,
       [x IN critical_equipment WHERE x IS NOT NULL] AS critical_equipment,
       failure_events,
       documents,
       [x IN uncovered_candidates WHERE x IS NOT NULL] AS uncovered_equipment
"""


def _retirement_points(years: int) -> int:
    if years <= 1:
        return 45
    if years <= 2:
        return 38
    if years <= 5:
        return 25
    if years <= 10:
        return 10
    return 0


def _severity(score: int) -> str:
    if score >= 70:
        return "critical"
    if score >= 40:
        return "elevated"
    return "monitored"


def build_person_risk(row: dict[str, Any]) -> dict[str, Any]:
    equipment = list(dict.fromkeys(row.get("equipment") or []))
    failures = list(dict.fromkeys(row.get("failure_events") or []))
    work_orders = list(dict.fromkeys(row.get("work_orders") or []))
    critical_equipment = list(dict.fromkeys(row.get("critical_equipment") or []))
    uncovered = list(dict.fromkeys(row.get("uncovered_equipment") or []))
    documents = list(dict.fromkeys(row.get("documents") or []))

    breadth_points = min(
        len(equipment) * 8 + len(failures) * 5 + len(work_orders) * 3,
        25,
    )
    score = min(
        _retirement_points(int(row["years_to_retirement"]))
        + breadth_points
        + min(len(critical_equipment) * 10, 10)
        + min(len(uncovered) * 8, 8),
        100,
    )

    total_assets = len(equipment)
    covered_assets = max(total_assets - len(uncovered), 0)
    coverage_pct = 100.0 if total_assets == 0 else round(covered_assets / total_assets * 100, 1)

    actions = []
    if score:
        actions.append(
            {
                "type": "capture_knowledge",
                "priority": _severity(score),
                "description": (
                    f"Capture operating knowledge from {row['name']} before "
                    f"their {row['years_to_retirement']}-year retirement horizon."
                ),
            }
        )
    if uncovered:
        actions.append(
            {
                "type": "assign_successor",
                "priority": "critical" if critical_equipment else "elevated",
                "equipment": uncovered,
                "description": "Assign a successor and validate knowledge transfer for uncovered assets.",
            }
        )

    return {
        "person_id": row["person_id"],
        "name": row["name"],
        "role": row.get("role"),
        "department": row.get("department"),
        "years_to_retirement": row["years_to_retirement"],
        "risk_score": score,
        "severity": _severity(score),
        "work_orders": work_orders,
        "equipment": equipment,
        "critical_equipment": critical_equipment,
        "failure_events": failures,
        "documents": documents,
        "uncovered_equipment": uncovered,
        "knowledge_coverage": {
            "covered_assets": covered_assets,
            "uncovered_assets": len(uncovered),
            "coverage_pct": coverage_pct,
        },
        "recommended_actions": actions,
    }


def list_knowledge_risks(session, retirement_horizon: int = 5) -> dict:
    rows = session.run(_RISK_QUERY, horizon=retirement_horizon).data()
    people = sorted(
        (
            build_person_risk(row)
            for row in rows
            if int(row["years_to_retirement"]) <= retirement_horizon
        ),
        key=lambda person: (-person["risk_score"], person["years_to_retirement"], person["name"]),
    )
    return {
        "summary": {
            "people_at_risk": len(people),
            "critical": sum(person["severity"] == "critical" for person in people),
            "elevated": sum(person["severity"] == "elevated" for person in people),
            "uncovered_assets": len(
                {
                    tag
                    for person in people
                    for tag in person["uncovered_equipment"]
                }
            ),
        },
        "retirement_horizon": retirement_horizon,
        "people": people,
    }


def get_person_knowledge_risk(session, person_id: str, retirement_horizon: int = 5) -> dict | None:
    rows = session.run(
        _RISK_QUERY.replace(
            "WHERE p.years_to_retirement <= $horizon",
            "WHERE p.person_id = $person_id",
        ),
        horizon=retirement_horizon,
        person_id=person_id,
    ).data()
    return build_person_risk(rows[0]) if rows else None
