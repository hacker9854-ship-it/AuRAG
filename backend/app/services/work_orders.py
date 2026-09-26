"""Persistent work-order drafts, edits, decisions, and audit history."""

import hashlib
from datetime import datetime, timezone
from uuid import uuid4


class WorkOrderConflict(Exception):
    def __init__(self, work_order_id: str):
        self.work_order_id = work_order_id
        super().__init__(f"Work order {work_order_id} changed since it was loaded.")


class WorkOrderNotFound(Exception):
    def __init__(self, work_order_id: str):
        self.work_order_id = work_order_id
        super().__init__(f"Work order {work_order_id} was not found.")


class InvalidWorkOrderTransition(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_draft_work_order(
    session,
    *,
    equipment_tag: str,
    description: str,
    recommended_action: str,
    actor: str,
    event_id: str | None = None,
    work_order_id: str | None = None,
    created_at: str | None = None,
) -> dict:
    if work_order_id is None and event_id:
        digest = hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:10].upper()
        work_order_id = f"WO-AI-{digest}"
    work_order_id = work_order_id or f"WO-AI-{uuid4().hex[:10].upper()}"
    created_at = created_at or _now()
    event_match = (
        "MATCH (event:PredictiveEvent {id:$event_id})"
        if event_id
        else "OPTIONAL MATCH (event:PredictiveEvent {id:$event_id})"
    )
    row = session.run(
        f"""
        MATCH (equipment:Equipment {{tag_id:$equipment_tag}})
        {event_match}
        MERGE (w:WorkOrder {{id:$work_order_id}})
        ON CREATE SET w.date = substring($created_at, 0, 10),
                      w.type = 'Corrective',
                      w.status = $status,
                      w.description = $description,
                      w.recommended_action = $recommended_action,
                      w.source = 'predictive_intelligence',
                      w.created_by = $actor,
                      w.created_at = $created_at,
                      w.updated_at = $created_at,
                      w.version = $version
        MERGE (w)-[:PERFORMED_ON]->(equipment)
        FOREACH (_ IN CASE WHEN event IS NULL THEN [] ELSE [1] END |
          MERGE (w)-[:TRIGGERED_BY]->(event)
        )
        RETURN w.id AS work_order_id
        """,
        equipment_tag=equipment_tag,
        event_id=event_id,
        work_order_id=work_order_id,
        status="Draft",
        description=description,
        recommended_action=recommended_action,
        actor=actor,
        created_at=created_at,
        version=1,
    ).single()
    if not row:
        raise WorkOrderNotFound(work_order_id)
    result = get_work_order(session, row["work_order_id"])
    if result is None:
        raise WorkOrderNotFound(work_order_id)
    return result


def update_work_order(
    session,
    work_order_id: str,
    *,
    expected_version: int,
    description: str,
    recommended_action: str,
    actor: str,
    updated_at: str | None = None,
) -> dict:
    row = session.run(
        """
        MATCH (w:WorkOrder {id:$work_order_id})
        WHERE w.version = $expected_version AND w.status IN ['Draft', 'In Review']
        SET w.description = $description,
            w.recommended_action = $recommended_action,
            w.updated_by = $actor,
            w.updated_at = $updated_at,
            w.status = 'In Review',
            w.version = w.version + 1
        CREATE (d:WorkOrderDecision {
          id:$decision_id,
          decision:'edit',
          actor:$actor,
          created_at:$updated_at,
          from_version:$expected_version,
          to_version:$next_version
        })
        MERGE (d)-[:DECISION_FOR]->(w)
        RETURN w.id AS work_order_id
        """,
        work_order_id=work_order_id,
        expected_version=expected_version,
        next_version=expected_version + 1,
        description=description,
        recommended_action=recommended_action,
        actor=actor,
        updated_at=updated_at or _now(),
        decision_id=f"WOD-{uuid4().hex.upper()}",
    ).single()
    if not row:
        raise WorkOrderConflict(work_order_id)
    result = get_work_order(session, row["work_order_id"])
    if result is None:
        raise WorkOrderNotFound(work_order_id)
    return result


def decide_work_order(
    session,
    work_order_id: str,
    *,
    decision: str,
    actor: str,
    expected_version: int,
    reason: str | None,
    decided_at: str | None = None,
) -> dict:
    if decision not in {"accept", "reject"}:
        raise ValueError("decision must be 'accept' or 'reject'")
    if decision == "reject" and not (reason or "").strip():
        raise ValueError("reject decision requires a reason")

    current = session.run(
        """
        MATCH (w:WorkOrder {id:$work_order_id})
        RETURN w.status AS status, w.version AS version
        """,
        work_order_id=work_order_id,
    ).single()
    if current is None:
        raise WorkOrderNotFound(work_order_id)
    if current["version"] != expected_version:
        raise WorkOrderConflict(work_order_id)
    if current["status"] not in {"Draft", "In Review"}:
        raise InvalidWorkOrderTransition(
            f"Cannot {decision} a work order in {current['status']} status."
        )

    decided_at = decided_at or _now()
    next_status = "Approved" if decision == "accept" else "Rejected"
    row = session.run(
        """
        MATCH (w:WorkOrder {id:$work_order_id})
        WHERE w.version = $expected_version
        SET w.status = $next_status,
            w.updated_by = $actor,
            w.updated_at = $decided_at,
            w.version = w.version + 1
        CREATE (d:WorkOrderDecision {
          id:$decision_id,
          decision:$decision,
          actor:$actor,
          reason:$reason,
          created_at:$decided_at,
          from_version:$expected_version,
          to_version:$next_version
        })
        MERGE (d)-[:DECISION_FOR]->(w)
        RETURN w.id AS work_order_id
        """,
        work_order_id=work_order_id,
        expected_version=expected_version,
        next_version=expected_version + 1,
        next_status=next_status,
        actor=actor,
        reason=(reason or "").strip() or None,
        decided_at=decided_at,
        decision=decision,
        decision_id=f"WOD-{uuid4().hex.upper()}",
    ).single()
    if not row:
        raise WorkOrderConflict(work_order_id)
    result = get_work_order(session, row["work_order_id"])
    if result is None:
        raise WorkOrderNotFound(work_order_id)
    return result


def get_work_order(session, work_order_id: str) -> dict | None:
    row = session.run(
        """
        MATCH (w:WorkOrder {id:$work_order_id})
        OPTIONAL MATCH (w)-[:PERFORMED_ON]->(e:Equipment)
        OPTIONAL MATCH (w)-[:TRIGGERED_BY]->(event:PredictiveEvent)
        OPTIONAL MATCH (decision:WorkOrderDecision)-[:DECISION_FOR]->(w)
        RETURN properties(w) AS work_order,
               e.tag_id AS equipment,
               event.id AS predictive_event_id,
               collect(DISTINCT properties(decision)) AS decisions
        """,
        work_order_id=work_order_id,
    ).single()
    if not row:
        return None
    return {
        **row["work_order"],
        "equipment": row.get("equipment"),
        "predictive_event_id": row.get("predictive_event_id"),
        "decisions": sorted(
            (decision for decision in row.get("decisions") or [] if decision),
            key=lambda item: item.get("created_at") or "",
        ),
    }


def list_work_orders(session, status: str | None = None, limit: int = 100) -> list[dict]:
    rows = session.run(
        """
        MATCH (w:WorkOrder)-[:PERFORMED_ON]->(e:Equipment)
        WHERE $status IS NULL OR w.status = $status
        OPTIONAL MATCH (w)-[:TRIGGERED_BY]->(event:PredictiveEvent)
        RETURN properties(w) AS work_order,
               e.tag_id AS equipment,
               event.id AS predictive_event_id
        ORDER BY coalesce(w.updated_at, w.date) DESC
        LIMIT $limit
        """,
        status=status,
        limit=limit,
    ).data()
    return [
        {
            **row["work_order"],
            "equipment": row.get("equipment"),
            "predictive_event_id": row.get("predictive_event_id"),
        }
        for row in rows
    ]
