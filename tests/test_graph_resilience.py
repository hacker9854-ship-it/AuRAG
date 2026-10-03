"""Unit and integration tests for Phase 3: Graph / AuraDB Resilience Verification.

Verifies:
- Task 3.1: Remote Neo4j connection checks and health diagnostics
- Task 3.2: Resilient fallback traversal (equipment, failure events, work orders, procedures, regulatory clauses)
- Task 3.3: Truthful readiness state (DEGRADED / FALLBACK during outage, never false ALL SYSTEMS NOMINAL)
- Task 3.4: Graph panel behavior (no key duplication, valid unique nodes, fallback identification)
- Task 3.5: Payment graph trail fallback and graph API deduplication
"""

import os
from unittest.mock import MagicMock, patch
import pytest
from starlette.testclient import TestClient

from backend.app.core.neo4j import (
    FallbackNeo4jSession,
    ResilientNeo4jSession,
    check_neo4j_health,
)
from backend.app.services.machine_money.graph import get_payment_graph_trail
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_check_neo4j_health_live_connection_success():
    """Verify check_neo4j_health reports ONLINE when driver connects successfully."""
    mock_driver = MagicMock()
    mock_driver.verify_connectivity.return_value = None

    with patch.dict(os.environ, {
        "NEO4J_URI": "neo4j+s://aura-demo.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "secret-aura-password",
        "NEO4J_DATABASE": "neo4j",
    }):
        with patch("backend.app.core.neo4j._get_neo4j_driver", return_value=mock_driver):
            health = check_neo4j_health()
            assert health["status"] == "ONLINE"
            assert health["state_label"] == "ONLINE"
            assert health["connected"] is True
            assert health["fallback_active"] is False
            assert "aura-demo.databases.neo4j.io" in health["uri"]


def test_check_neo4j_health_remote_connection_failure():
    """Verify check_neo4j_health gracefully degrades without crashing when remote Neo4j fails."""
    mock_driver = MagicMock()
    mock_driver.verify_connectivity.side_effect = ConnectionError("AuraDB sandbox paused or unreachable (503 Service Unavailable)")

    with patch.dict(os.environ, {
        "NEO4J_URI": "neo4j+s://aura-demo.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "secret-aura-password",
    }):
        with patch("backend.app.core.neo4j._get_neo4j_driver", return_value=mock_driver):
            health = check_neo4j_health()
            assert health["status"] == "DEGRADED"
            assert health["state_label"] == "DEGRADED / FALLBACK"
            assert health["connected"] is False
            assert health["fallback_active"] is True
            assert "Remote Neo4j connectivity check failed" in health["detail"]


def test_check_neo4j_health_missing_credentials():
    """Verify missing credentials immediately returns DEGRADED / FALLBACK state."""
    with patch.dict(os.environ, {"NEO4J_URI": "", "NEO4J_USERNAME": "", "NEO4J_PASSWORD": ""}):
        health = check_neo4j_health()
        assert health["status"] == "DEGRADED"
        assert health["state_label"] == "DEGRADED / FALLBACK"
        assert health["connected"] is False
        assert health["fallback_active"] is True


def test_fallback_traversal_equipment_and_replay_asset():
    """Verify fallback session correctly traverses P-101, P-101A, and REPLAY-ASSET-01."""
    session = FallbackNeo4jSession()

    # 1. Equipment tag listing
    discovery = session.run("MATCH (e:Equipment) RETURN e.tag_id AS t").data()
    tag_ids = {row["t"] for row in discovery}
    assert "P-101A" in tag_ids
    assert "REPLAY-ASSET-01" in tag_ids

    # 2. Multi-hop traversal query for P-101A
    res_p101a = session.run(
        "MATCH (e:Equipment {tag_id:$tag}) ... RETURN failure_events, work_orders, procedures, clauses",
        tag="P-101A"
    ).data()
    assert len(res_p101a) > 0
    row_a = res_p101a[0]
    assert any(fe["id"] == "FE-001" for fe in row_a["failure_events"])
    assert any(wo["id"] == "WO-1001" for wo in row_a["work_orders"])
    assert any(proc["id"] == "PROC-001" for proc in row_a["procedures"])

    # 3. Multi-hop traversal query for REPLAY-ASSET-01 (NASA replay asset)
    res_replay = session.run(
        "MATCH (e:Equipment {tag_id:$tag}) ... RETURN failure_events, work_orders, procedures, clauses",
        tag="REPLAY-ASSET-01"
    ).data()
    assert len(res_replay) > 0
    row_r = res_replay[0]
    assert any(fe["id"] == "FE-001" for fe in row_r["failure_events"])

    # 4. Compressor C-201 traversal with Section 37 regulatory clause
    res_c201 = session.run(
        "MATCH (e:Equipment {tag_id:$tag}) ... RETURN failure_events, work_orders, procedures, clauses",
        tag="C-201"
    ).data()
    row_c = res_c201[0]
    assert any(cl["id"] == "FACT1948-S37" for cl in row_c["clauses"])


def test_payment_graph_trail_fallback():
    """Verify operational graph trail works truthfully in fallback mode with explicit labeling."""
    session = FallbackNeo4jSession()
    trail = get_payment_graph_trail(session, payment_id="PAY-TEST-999")

    assert trail["found"] is True
    assert trail["is_fallback"] is True
    assert trail["graph_status"] == "DEGRADED / FALLBACK"
    assert trail["work_order"]["id"] == "WO-2026-P101"
    assert trail["predictive_trigger"]["event_id"] == "EVT-VIB-001"
    assert trail["failure_signature"]["failure_id"] == "FE-001"
    assert len(trail["graph_story"]) == 5


def test_graph_health_endpoint(client):
    """Verify /api/graph/health returns truthful diagnostic schema."""
    resp = client.get("/api/graph/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "state_label" in data
    assert "connected" in data
    assert "fallback_active" in data
    assert data["state_label"] in ("ONLINE", "DEGRADED / FALLBACK")


def test_graph_api_deduplication_and_truthful_status(client):
    """Verify /api/graph deduplicates identical node IDs and returns truthful graph_status."""
    # Request overlapping paths with duplicated citations
    payload = {
        "graph_paths": [
            {"type": "Equipment", "id": "P-101A"},
            {"type": "FailureEvent", "id": "FE-001"},
            {"type": "Equipment", "id": "P-101A"},  # duplicate intentional
            {"type": "Procedure", "id": "PROC-001"},
        ]
    }
    resp = client.post("/api/graph", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # Check deduplication
    node_ids = [n["id"] for n in data["nodes"]]
    assert len(node_ids) == len(set(node_ids)), f"Duplicate node IDs found: {node_ids}"

    # Check truthful status metadata
    assert "graph_status" in data
    assert data["graph_status"] in ("ONLINE", "DEGRADED / FALLBACK")
    assert "fallback_active" in data
    assert isinstance(data["fallback_active"], bool)


def test_resilient_session_transparent_fallback():
    """Verify ResilientNeo4jSession falls back to FallbackNeo4jSession if live session fails."""
    mock_real = MagicMock()
    mock_real.run.side_effect = Exception("Neo4j database connection terminated unexpectedly")

    resilient = ResilientNeo4jSession(real_session=mock_real)
    assert resilient.is_live is True  # initially attempts live

    # Execute query that crashes real session
    res = resilient.run("MATCH (e:Equipment) RETURN e.tag_id AS t")
    data = res.data()

    # Verify fallback seamlessly delivered data without crashing
    assert len(data) >= 5
    assert any(row.get("t") == "P-101A" for row in data)
    assert resilient.is_live is False  # correctly marked not live after failure
