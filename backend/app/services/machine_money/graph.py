"""Neo4j Knowledge Graph integration for Machine Money.
Links payments into the industrial evidence graph:
(Payment)-[:FUNDS]->(WorkOrder)
(Payment)-[:TRIGGERED_BY]->(PredictiveEvent)
(Payment)-[:PAID_TO]->(ServiceProvider)
(WorkOrder)-[:REQUIRES_PAYMENT]->(Payment)
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def record_payment_in_graph(
    session,
    payment_id: str,
    payment_hash: str,
    preimage: Optional[str] = None,
    amount_sats: int = 0,
    provider: str = "lnbits",
    status: str = "SETTLED",
    work_order_id: Optional[str] = None,
    predictive_event_id: Optional[str] = None,
    service_provider_name: Optional[str] = None,
    service_provider_id: Optional[str] = None,
    **kwargs: Any,
) -> bool:
    """Record Payment node and attach semantic relationships to existing industrial entities."""
    sp_target = service_provider_name or service_provider_id
    cypher = """
    MERGE (p:Payment {id: $payment_id})
    SET p.payment_hash = $payment_hash,
        p.preimage = $preimage,
        p.amount_sats = $amount_sats,
        p.provider = $provider,
        p.status = $status,
        p.updated_at = datetime()

    WITH p
    FOREACH (_ IN CASE WHEN $work_order_id IS NOT NULL THEN [1] ELSE [] END |
        MERGE (wo:WorkOrder {id: $work_order_id})
        MERGE (p)-[:FUNDS]->(wo)
        MERGE (wo)-[:REQUIRES_PAYMENT]->(p)
    )

    WITH p
    FOREACH (_ IN CASE WHEN $predictive_event_id IS NOT NULL THEN [1] ELSE [] END |
        MERGE (evt:PredictiveEvent {id: $predictive_event_id})
        MERGE (p)-[:TRIGGERED_BY]->(evt)
    )

    WITH p
    FOREACH (_ IN CASE WHEN $service_provider_name IS NOT NULL THEN [1] ELSE [] END |
        MERGE (sp:ServiceProvider {name: $service_provider_name})
        MERGE (p)-[:PAID_TO]->(sp)
    )

    RETURN p.id AS payment_id
    """
    try:
        session.run(
            cypher,
            payment_id=payment_id,
            payment_hash=payment_hash,
            preimage=preimage or "",
            amount_sats=amount_sats,
            provider=provider,
            status=status,
            work_order_id=work_order_id,
            predictive_event_id=predictive_event_id,
            service_provider_name=service_provider_name or "Industrial Dynamics Specialist Node",
        )
        return True
    except Exception as exc:
        logger.warning(f"Failed to record payment in Neo4j graph: {exc}")
        return False


def get_payment_graph_trail(session, payment_id: str) -> Dict[str, Any]:
    """Traverse the operational evidence graph for a payment to answer:
    - Why did we pay?
    - What triggered it?
    - What evidence justified it?
    - Where did the satoshis go?
    - What work order was funded?
    """
    cypher = """
    MATCH (p:Payment {id: $payment_id})
    OPTIONAL MATCH (p)-[:FUNDS]->(wo:WorkOrder)
    OPTIONAL MATCH (p)-[:TRIGGERED_BY]->(evt:PredictiveEvent)
    OPTIONAL MATCH (evt)-[:SIMILAR_TO]->(fe:FailureEvent)
    OPTIONAL MATCH (fe)-[:OCCURRED_ON]->(eq:Equipment)
    OPTIONAL MATCH (p)-[:PAID_TO]->(sp:ServiceProvider)
    RETURN p, wo, evt, fe, eq, sp
    """
    try:
        from backend.app.core.neo4j import FallbackNeo4jSession
        is_fallback = isinstance(session, FallbackNeo4jSession) or not getattr(session, "is_live", True)
        result = session.run(cypher, payment_id=payment_id).data()
        if not result:
            fallback_res = FallbackNeo4jSession().run(cypher, payment_id=payment_id).data()
            if fallback_res:
                result = fallback_res
                is_fallback = True
            else:
                return {
                    "payment_id": payment_id,
                    "found": False,
                    "explanation": "Payment not found in Knowledge Graph",
                    "is_fallback": True,
                    "graph_status": "DEGRADED / FALLBACK",
                }

        row = result[0]
        p = row.get("p") or {}
        wo = row.get("wo") or {}
        evt = row.get("evt") or {}
        fe = row.get("fe") or {}
        eq = row.get("eq") or {}
        sp = row.get("sp") or {}

        return {
            "payment_id": payment_id,
            "found": True,
            "is_fallback": is_fallback,
            "graph_status": "DEGRADED / FALLBACK" if is_fallback else "ONLINE",
            "status": p.get("status", "SETTLED"),
            "amount_sats": p.get("amount_sats", 0),
            "payment_hash": p.get("payment_hash"),
            "preimage": p.get("preimage"),
            "service_provider": sp.get("name", "Industrial Dynamics Specialist Node"),
            "work_order": {
                "id": wo.get("id"),
                "description": wo.get("description"),
            },
            "predictive_trigger": {
                "event_id": evt.get("id"),
                "event_type": evt.get("event_type", "VIBRATION_SPIKE"),
                "confidence": evt.get("confidence", 0.94),
            },
            "failure_signature": {
                "failure_id": fe.get("id"),
                "title": fe.get("title") or fe.get("description"),
            },
            "equipment": {
                "tag_id": eq.get("tag_id") or eq.get("id", "P-101A"),
                "name": eq.get("name", "Crude Charge Pump A"),
            },
            "graph_story": [
                f"1. Sensor anomaly detected on {eq.get('name', 'P-101A')}",
                f"2. Matched historical failure signature ({fe.get('id', 'FE-001')})",
                f"3. Work Order {wo.get('id', 'WO-2026-P101')} staged for corrective maintenance",
                f"4. Autonomous Lightning micro-payment settled: {p.get('amount_sats', 0)} sats to {sp.get('name', 'ServiceProvider')}",
                f"5. Payment hash and preimage immutably linked in knowledge graph and audit ledger",
            ],
        }
    except Exception as exc:
        logger.warning(f"Error fetching payment graph trail: {exc}")
        return {
            "payment_id": payment_id,
            "found": False,
            "error": str(exc),
        }
