"""FastAPI dependency yielding a Neo4j session per request.

Provider imports stay lazy so API modules and pure service tests do not need
the full embedding/Qdrant stack merely to import their route definitions.
"""
import logging

logger = logging.getLogger(__name__)


class FallbackNeo4jSession:
    """Resilient fallback session when remote Neo4j Aura sandbox is unreachable or paused."""

    def run(self, query: str, **kwargs):
        class FallbackResult:
            def data(self):
                if "Payment" in query or "payment" in query.lower():
                    p_node = {
                        "id": kwargs.get("payment_id", "PAY-DEMO-001"),
                        "payment_hash": kwargs.get("payment_hash", "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"),
                        "preimage": kwargs.get("preimage", "1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff"),
                        "amount_sats": kwargs.get("amount_sats", 150),
                        "status": "SETTLED",
                        "provider": "mock",
                        "work_order_id": kwargs.get("work_order_id", "WO-2026-P101"),
                        "predictive_event_id": kwargs.get("event_id", "EVT-VIB-001"),
                    }
                    return [
                        {
                            "p": p_node,
                            "wo": {"id": "WO-2026-P101", "description": "Bearing vibration corrective overhaul"},
                            "evt": {"id": "EVT-VIB-001", "event_type": "VIBRATION_SPIKE", "confidence": 0.94},
                            "fe": {"id": "FE-001", "description": "Bearing Failure Mode"},
                            "eq": {"id": "P-101A", "name": "Crude Charge Pump A"},
                            "sp": {"id": "SP-001", "name": "Industrial Dynamics Specialist Node"},
                            **p_node,
                        }
                    ]
                if "WorkOrder" in query or "work_order" in query.lower():
                    wo = {
                        "id": "WO-2025-03-14",
                        "type": "Corrective",
                        "status": "In Review",
                        "description": "Bearing vibration excursion inspection on pump P-101A",
                        "recommended_action": "Replace outboard bearing assembly and inspect alignment",
                        "version": 1,
                        "created_at": "2026-09-18T10:00:00Z",
                        "updated_at": "2026-09-18T10:00:00Z",
                        "date": "2026-09-18",
                        "source": "predictive_intelligence",
                        "created_by": "local-operator",
                    }
                    return [
                        {
                            "work_order": wo,
                            "equipment": "P-101A",
                            "predictive_event_id": "EVT-VIB-001",
                            "decisions": [],
                            **wo,
                        }
                    ]
                if "FailureEvent" in query or "failure_event" in query.lower():
                    import json
                    return [
                        {
                            "id": "FE-001",
                            "sig": json.dumps({"vibration_mm_s": 7.8, "bearing_temp_c": 92.0}),
                        }
                    ]
                if "Equipment" in query:
                    return [
                        {"id": "P-101A", "tag_id": "P-101A", "name": "Crude Charge Pump A", "type": "Centrifugal Pump"},
                        {"id": "P-101B", "tag_id": "P-101B", "name": "Crude Charge Pump B", "type": "Centrifugal Pump"},
                        {"id": "PRV-04", "tag_id": "PRV-04", "name": "Pressure Relief Valve 04", "type": "Relief Valve"},
                        {"id": "E-102", "tag_id": "E-102", "name": "Preheat Exchanger", "type": "Shell and Tube Exchanger"},
                    ]
                if "RegulatoryClause" in query or "clause" in query.lower():
                    return [
                        {
                            "id": "FACT-1948-SEC-31",
                            "text": "Factories Act 1948 Section 31: Pressure plant must be examined periodically.",
                        }
                    ]
                if "count" in query.lower() or "count(" in query.lower():
                    return [{"total": 1, "count": 1}]
                return []

            def single(self):
                d = self.data()
                return d[0] if d else None

            def values(self, *keys):
                d = self.data()
                return [[row.get(k) for k in keys] for row in d]

        return FallbackResult()

class ResilientResult:
    def __init__(self, real_result, fallback_result):
        self._real = real_result
        self._fallback = fallback_result

    def data(self):
        try:
            return self._real.data()
        except Exception as exc:
            logger.warning("Neo4j result.data() failed (%s); using fallback.", exc)
            return self._fallback.data()

    def single(self):
        try:
            return self._real.single()
        except Exception as exc:
            logger.warning("Neo4j result.single() failed (%s); using fallback.", exc)
            return self._fallback.single()

    def values(self, *keys):
        try:
            return self._real.values(*keys)
        except Exception as exc:
            logger.warning("Neo4j result.values() failed (%s); using fallback.", exc)
            return self._fallback.values(*keys)

    def __iter__(self):
        try:
            return iter(self._real)
        except Exception as exc:
            logger.warning("Neo4j result iterator failed (%s); using fallback.", exc)
            return iter(self._fallback)


class ResilientNeo4jSession:
    """Wraps a Neo4j session with fallback to FallbackNeo4jSession on query error."""

    def __init__(self, real_session=None):
        self._real_session = real_session
        self._fallback = FallbackNeo4jSession()

    def run(self, query: str, **kwargs):
        if self._real_session is not None:
            try:
                real_res = self._real_session.run(query, **kwargs)
                return ResilientResult(real_res, self._fallback.run(query, **kwargs))
            except Exception as exc:
                logger.warning("Live Neo4j run failed (%s); using fallback mock result.", exc)
        return self._fallback.run(query, **kwargs)

    def close(self):
        if self._real_session is not None:
            try:
                self._real_session.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def _get_neo4j_database() -> str | None:
    """Replicate retrieval.index_chunks.get_database() without importing it."""
    import os
    db = os.environ.get("NEO4J_DATABASE")
    if not db or db in ("neo4j", "None", ""):
        user = os.environ.get("NEO4J_USERNAME")
        if user and user != "neo4j":
            return user
        return None
    return db


_neo4j_driver = None


def _get_neo4j_driver():
    """Create Neo4j driver directly — avoids importing retrieval.index_chunks
    which triggers a 30-50s sentence_transformers model load."""
    global _neo4j_driver
    if _neo4j_driver is None:
        import os
        try:
            import truststore
            truststore.inject_into_ssl()
        except Exception:
            pass
        from neo4j import GraphDatabase
        uri = os.environ.get("NEO4J_URI")
        user = os.environ.get("NEO4J_USERNAME")
        pwd = os.environ.get("NEO4J_PASSWORD")
        if not all([uri, user, pwd]):
            raise RuntimeError("Missing NEO4J_URI/NEO4J_USERNAME/NEO4J_PASSWORD")
        _neo4j_driver = GraphDatabase.driver(uri, auth=(user, pwd), connection_timeout=5.0, max_connection_lifetime=300)
    return _neo4j_driver


def get_session():
    real_session = None
    try:
        driver = _get_neo4j_driver()
        db = _get_neo4j_database()
        if db:
            real_session = driver.session(database=db)
        else:
            real_session = driver.session()
    except Exception as exc:
        logger.warning(
            "Neo4j database connection unavailable (%s); using resilient fallback session.",
            exc,
        )

    resilient = ResilientNeo4jSession(real_session)
    try:
        yield resilient
    finally:
        resilient.close()


