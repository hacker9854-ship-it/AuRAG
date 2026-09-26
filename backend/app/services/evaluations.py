"""Durable RAGAS evaluation records stored in Neo4j."""

import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _loads(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def create_evaluation(
    session,
    *,
    score_id: str,
    query: str,
    answer: str,
    routed_agent: str,
    citations: list[str],
    graph_paths: list[dict],
    retrieved_context: list,
    created_at: str | None = None,
) -> dict:
    created_at = created_at or _utc_now()
    params = {
        "score_id": score_id,
        "user_query": query,
        "answer": answer,
        "routed_agent": routed_agent,
        "citations_json": _json(citations),
        "graph_paths_json": _json(graph_paths),
        "retrieved_context_json": _json(retrieved_context),
        "created_at": created_at,
    }
    session.run(
        """
        MERGE (e:EvaluationRun {score_id:$score_id})
        SET e.query = $user_query,
            e.answer = $answer,
            e.routed_agent = $routed_agent,
            e.citations_json = $citations_json,
            e.graph_paths_json = $graph_paths_json,
            e.retrieved_context_json = $retrieved_context_json,
            e.created_at = $created_at,
            e.ragas_status = 'scoring',
            e.low_faithfulness = false
        """,
        **params,
    )
    return {
        **params,
        "citations": citations,
        "graph_paths": graph_paths,
        "retrieved_context": retrieved_context,
        "ragas_status": "scoring",
        "ragas_scores": {},
        "low_faithfulness": False,
    }


def update_evaluation(
    session,
    score_id: str,
    *,
    status: str,
    scores: dict[str, float] | None = None,
    low_faithfulness: bool = False,
    duration_ms: int | None = None,
    completed_at: str | None = None,
    detail: str | None = None,
) -> None:
    scores = scores or {}
    session.run(
        """
        MATCH (e:EvaluationRun {score_id:$score_id})
        SET e.ragas_status = $status,
            e.faithfulness = $faithfulness,
            e.context_precision = $context_precision,
            e.answer_relevancy = $answer_relevancy,
            e.low_faithfulness = $low_faithfulness,
            e.scoring_duration_ms = $duration_ms,
            e.completed_at = $completed_at,
            e.detail = $detail
        """,
        score_id=score_id,
        status=status,
        faithfulness=scores.get("faithfulness"),
        context_precision=scores.get("context_precision"),
        answer_relevancy=scores.get("answer_relevancy"),
        low_faithfulness=low_faithfulness,
        duration_ms=duration_ms,
        completed_at=completed_at or _utc_now(),
        detail=detail,
    )


def deserialize_evaluation(record: dict) -> dict:
    scores = {}
    if record.get("ragas_status") == "scored":
        scores = {
            "faithfulness": record.get("faithfulness"),
            "context_precision": record.get("context_precision"),
            "answer_relevancy": record.get("answer_relevancy"),
        }
    return {
        "score_id": record.get("score_id"),
        "query": record.get("query"),
        "answer": record.get("answer"),
        "routed_agent": record.get("routed_agent"),
        "citations": _loads(record.get("citations_json"), []),
        "graph_paths": _loads(record.get("graph_paths_json"), []),
        "retrieved_context": _loads(record.get("retrieved_context_json"), []),
        "ragas_status": record.get("ragas_status"),
        "ragas_scores": scores,
        "low_faithfulness": bool(record.get("low_faithfulness")),
        "created_at": record.get("created_at"),
        "completed_at": record.get("completed_at"),
        "scoring_duration_ms": record.get("scoring_duration_ms"),
        "detail": record.get("detail"),
    }


def get_evaluation(session, score_id: str) -> dict | None:
    row = session.run(
        "MATCH (e:EvaluationRun {score_id:$score_id}) RETURN properties(e) AS evaluation",
        score_id=score_id,
    ).single()
    return deserialize_evaluation(row["evaluation"]) if row else None


def list_evaluations(
    session,
    *,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    agent: str | None = None,
    low_faithfulness: bool | None = None,
) -> list[dict]:
    rows = session.run(
        """
        MATCH (e:EvaluationRun)
        WHERE ($status IS NULL OR e.ragas_status = $status)
          AND ($agent IS NULL OR e.routed_agent = $agent)
          AND ($low_faithfulness IS NULL OR e.low_faithfulness = $low_faithfulness)
        RETURN properties(e) AS evaluation
        ORDER BY e.created_at DESC
        SKIP $offset LIMIT $limit
        """,
        status=status,
        agent=agent,
        low_faithfulness=low_faithfulness,
        offset=offset,
        limit=limit,
    ).data()
    return [deserialize_evaluation(row["evaluation"]) for row in rows]


def count_evaluations(
    session,
    *,
    status: str | None = None,
    agent: str | None = None,
    low_faithfulness: bool | None = None,
) -> int:
    row = session.run(
        """
        MATCH (e:EvaluationRun)
        WHERE ($status IS NULL OR e.ragas_status = $status)
          AND ($agent IS NULL OR e.routed_agent = $agent)
          AND ($low_faithfulness IS NULL OR e.low_faithfulness = $low_faithfulness)
        RETURN count(e) AS total
        """,
        status=status,
        agent=agent,
        low_faithfulness=low_faithfulness,
    ).single()
    return int((row or {}).get("total") or 0)


def summarize_evaluations_db(session) -> dict:
    """Aggregate the complete durable history without a pagination cap."""
    overview = session.run(
        """
        MATCH (e:EvaluationRun)
        RETURN count(e) AS total,
               sum(CASE WHEN e.low_faithfulness THEN 1 ELSE 0 END) AS low_count,
               avg(e.faithfulness) AS faithfulness,
               avg(e.context_precision) AS context_precision,
               avg(e.answer_relevancy) AS answer_relevancy
        """
    ).single() or {}
    status_rows = session.run(
        """
        MATCH (e:EvaluationRun)
        RETURN coalesce(e.ragas_status, 'unknown') AS key, count(*) AS count
        """
    ).data()
    agent_rows = session.run(
        """
        MATCH (e:EvaluationRun)
        RETURN coalesce(e.routed_agent, 'unknown') AS key, count(*) AS count
        """
    ).data()
    trend_rows = session.run(
        """
        MATCH (e:EvaluationRun)
        WHERE e.created_at IS NOT NULL
        WITH substring(e.created_at, 0, 10) AS day, e
        RETURN day,
               count(e) AS total,
               avg(e.faithfulness) AS faithfulness,
               avg(e.context_precision) AS context_precision,
               avg(e.answer_relevancy) AS answer_relevancy,
               sum(CASE WHEN e.low_faithfulness THEN 1 ELSE 0 END) AS low_count
        ORDER BY day DESC
        LIMIT 30
        """
    ).data()

    def rounded(value):
        return round(float(value), 3) if value is not None else None

    return {
        "total": int(overview.get("total") or 0),
        "status_counts": {row["key"]: row["count"] for row in status_rows},
        "agent_counts": {row["key"]: row["count"] for row in agent_rows},
        "low_faithfulness_count": int(overview.get("low_count") or 0),
        "averages": {
            "faithfulness": rounded(overview.get("faithfulness")),
            "context_precision": rounded(overview.get("context_precision")),
            "answer_relevancy": rounded(overview.get("answer_relevancy")),
        },
        "trend": [
            {
                "day": row["day"],
                "total": int(row.get("total") or 0),
                "faithfulness": rounded(row.get("faithfulness")),
                "context_precision": rounded(row.get("context_precision")),
                "answer_relevancy": rounded(row.get("answer_relevancy")),
                "low_faithfulness_count": int(row.get("low_count") or 0),
            }
            for row in reversed(trend_rows)
        ],
    }


def summarize_evaluations(evaluations: list[dict]) -> dict:
    status_counts = Counter(item.get("ragas_status") or "unknown" for item in evaluations)
    agent_counts = Counter(item.get("routed_agent") or "unknown" for item in evaluations)
    scored = [item for item in evaluations if item.get("ragas_status") == "scored"]

    averages = {}
    for metric in ("faithfulness", "context_precision", "answer_relevancy"):
        values = [
            item.get("ragas_scores", {}).get(metric)
            for item in scored
            if item.get("ragas_scores", {}).get(metric) is not None
        ]
        averages[metric] = round(sum(values) / len(values), 3) if values else None

    return {
        "total": len(evaluations),
        "status_counts": dict(status_counts),
        "agent_counts": dict(agent_counts),
        "low_faithfulness_count": sum(
            bool(item.get("low_faithfulness")) for item in evaluations
        ),
        "averages": averages,
        "trend": [],
    }


def create_remediation(
    db,
    *,
    score_id: str,
    user_id: str,
    site_id: str = "plant-mumbai-01",
    reason: str,
    incorrect_snippets: list[str] | None = None,
    correction_notes: str,
) -> dict:
    """Flag an answer or evidence chunk as incorrect and queue for re-indexing."""
    from backend.app.db.models import AuditEvent, EvaluationRemediation

    incorrect_snippets = incorrect_snippets or []
    remediation = EvaluationRemediation(
        score_id=score_id,
        user_id=user_id,
        site_id=site_id,
        reason=reason,
        incorrect_snippets_json=json.dumps(incorrect_snippets),
        correction_notes=correction_notes,
        status="PENDING_REINDEX",
    )
    db.add(remediation)
    db.flush()

    audit = AuditEvent(
        user_id=user_id,
        site_id=site_id,
        role="ReliabilityEngineer",
        action_type="EVALUATION_REMEDIATION_SUBMITTED",
        resource_type="evaluation_remediation",
        resource_id=remediation.remediation_id,
        details_json=json.dumps({"score_id": score_id, "reason": reason}),
        status="SUCCESS",
    )
    db.add(audit)
    db.commit()
    db.refresh(remediation)
    return remediation.to_dict()


def list_remediations(
    db,
    *,
    site_id: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """List operational remediation records."""
    from backend.app.db.models import EvaluationRemediation

    query = db.query(EvaluationRemediation)
    if site_id:
        query = query.filter(EvaluationRemediation.site_id == site_id)
    if status:
        query = query.filter(EvaluationRemediation.status == status)
    records = query.order_by(EvaluationRemediation.created_at.desc()).all()
    return [r.to_dict() for r in records]


def update_remediation_status(
    db,
    *,
    remediation_id: str,
    status: str,
    resolved_by: str,
) -> dict | None:
    """Update remediation status (e.g. REINDEXED or RESOLVED)."""
    from backend.app.db.models import AuditEvent, EvaluationRemediation

    item = db.query(EvaluationRemediation).filter(EvaluationRemediation.remediation_id == remediation_id).first()
    if not item:
        return None

    item.status = status
    if status in ("REINDEXED", "RESOLVED"):
        item.resolved_at = datetime.now(timezone.utc)
        item.resolved_by = resolved_by

    audit = AuditEvent(
        user_id=resolved_by,
        site_id=item.site_id,
        role="AutomationAdmin",
        action_type="EVALUATION_REMEDIATION_STATUS_UPDATED",
        resource_type="evaluation_remediation",
        resource_id=item.remediation_id,
        details_json=json.dumps({"new_status": status}),
        status="SUCCESS",
    )
    db.add(audit)
    db.commit()
    db.refresh(item)
    return item.to_dict()

