"""Durable proactive predictive events and notification payloads."""

import json
import os
import hashlib
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def predictive_event_identity(
    equipment_tag: str,
    failure_event_id: str,
    detected_at: str,
    cooldown_seconds: int = 1800,
) -> tuple[str, str]:
    """Create a durable identity shared by retries and worker restarts."""
    moment = datetime.fromisoformat(detected_at.replace("Z", "+00:00"))
    bucket = int(moment.timestamp()) // max(cooldown_seconds, 1)
    dedupe_key = f"{equipment_tag}|{failure_event_id}|{bucket}"
    digest = hashlib.sha256(dedupe_key.encode("utf-8")).hexdigest()[:12].upper()
    return dedupe_key, f"PE-{bucket:010d}-{digest}"


def create_predictive_event(
    session,
    *,
    event_id: str | None = None,
    equipment_tag: str,
    failure_event_id: str,
    similarity: float,
    symptom: str,
    reading: dict,
    detected_at: str | None = None,
    cooldown_seconds: int = 1800,
) -> dict:
    detected_at = detected_at or _now()
    dedupe_key, stable_id = predictive_event_identity(
        equipment_tag,
        failure_event_id,
        detected_at,
        cooldown_seconds,
    )
    event_id = event_id or stable_id
    row = session.run(
        """
        MERGE (event:PredictiveEvent {dedupe_key:$dedupe_key})
        ON CREATE SET event.detected_at = $detected_at,
                      event.status = 'unread',
                      event.id = $event_id
        SET event.equipment = $equipment_tag,
            event.failure_event_id = $failure_event_id,
            event.similarity = $similarity,
            event.symptom = $symptom,
            event.reading_json = $reading_json,
            event.updated_at = $detected_at
        WITH event
        MATCH (equipment:Equipment {tag_id:$equipment_tag})
        MERGE (event)-[:TRIGGERS]->(equipment)
        WITH event
        OPTIONAL MATCH (failure:FailureEvent {id:$failure_event_id})
        FOREACH (_ IN CASE WHEN failure IS NULL THEN [] ELSE [1] END |
          MERGE (event)-[:MATCHES]->(failure)
        )
        WITH event
        MERGE (notification:Notification {id:$event_id})
        SET notification.type = 'predictive_warning',
            notification.status = event.status,
            notification.title = $title,
            notification.description = $symptom,
            notification.severity = 'high',
            notification.created_at = event.detected_at
        MERGE (notification)-[:ABOUT]->(event)
        RETURN properties(event) AS event,
               event.detected_at = $detected_at AS created
        """,
        event_id=event_id,
        dedupe_key=dedupe_key,
        equipment_tag=equipment_tag,
        failure_event_id=failure_event_id,
        similarity=similarity,
        symptom=symptom,
        reading_json=json.dumps(reading, ensure_ascii=False, separators=(",", ":")),
        detected_at=detected_at,
        title=f"{equipment_tag} requires attention",
    ).single()
    if not row:
        return None
    return {**row["event"], "_created": bool(row.get("created", True))}


def list_predictive_events(session, *, since: str | None = None, limit: int = 50) -> list[dict]:
    try:
        rows = session.run(
            """
            MATCH (event:PredictiveEvent)
            WHERE $since IS NULL OR event.id > $since
            RETURN properties(event) AS event
            ORDER BY event.id ASC
            LIMIT $limit
            """,
            since=since,
            limit=limit,
        ).data()
        return [row["event"] for row in rows]
    except Exception:
        return []



def mark_notification_read(session, event_id: str) -> bool:
    row = session.run(
        """
        MATCH (notification:Notification {id:$event_id})
        SET notification.status = 'read'
        WITH notification
        OPTIONAL MATCH (event:PredictiveEvent {id:$event_id})
        SET event.status = 'read'
        RETURN notification.id AS id
        """,
        event_id=event_id,
    ).single()
    return bool(row)


def notification_payload(event: dict) -> dict:
    return {
        "id": event["id"],
        "type": "predictive_warning",
        "title": f"{event['equipment']} requires attention",
        "description": event["symptom"],
        "severity": "high",
        "equipment": event["equipment"],
        "failure_event_id": event["failure_event_id"],
        "similarity": event["similarity"],
        "status": event.get("status", "unread"),
        "detected_at": event.get("detected_at"),
        "action_href": f"/predictive-watch?event={event['id']}",
    }


def publish_event(event_id: str) -> None:
    """Best-effort Redis fan-out; Neo4j remains the durable source."""
    try:
        from redis import Redis

        Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379")).publish(
            "aurag:predictive-events",
            event_id,
        )
    except Exception as exc:
        print(f"[events] Redis publish skipped: {exc}")
