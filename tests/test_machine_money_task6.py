"""Comprehensive tests for Task 6: Telemetry Trigger, Agent Integration & GraphRAG Evidence Link."""
import os
import pytest
from fastapi.testclient import TestClient

from backend.app.db.database import get_db, init_db
from backend.app.db.models import PaymentRecord
from backend.app.main import app
from backend.app.services.machine_money.bridge import (
    build_operational_evidence_package,
    map_telemetry_to_service,
)
from backend.app.services.machine_money.schemas import PaymentStatus

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_env():
    os.environ["MACHINE_MONEY_PROVIDER"] = "mock"
    os.environ["MACHINE_MONEY_AUTO_PAY_ENABLED"] = "true"
    os.environ["MACHINE_MONEY_MAX_AUTOPAY_SATS"] = "500"
    init_db()


def test_evidence_package_contract():
    """Verify operational evidence package answers 'Why did the agent spend money?' (Section 18)."""
    pkg = build_operational_evidence_package(
        session=None,
        equipment_tag="P-101",
        event_id="EVT-TEST-001",
        confidence=0.91,
    )
    assert pkg["equipment"] == "P-101"
    assert pkg["confidence"] == 0.91
    assert "FE-001" in pkg["evidence"]
    assert "WO-1002" in pkg["evidence"]
    assert "PROC-001" in pkg["evidence"]
    assert "Because P-101 matched failure signature FE-001" in pkg["cross_layer_justification"]
    assert "WO-1002 shows overdue" in pkg["cross_layer_justification"]
    assert "PROC-001 recommends" in pkg["cross_layer_justification"]


def test_telemetry_service_mapping():
    """Verify predictive anomaly characteristics correctly map to catalog services (Section 16)."""
    assert map_telemetry_to_service("P-101A") == "bearing-inspection"
    assert map_telemetry_to_service("E-102", symptom="thermal gradient breach") == "thermal-diagnostics"
    assert map_telemetry_to_service("C-201", symptom="oil viscosity loss") == "oil-tribology-analysis"
    assert map_telemetry_to_service("T-301", symptom="shaft misalignment") == "laser-shaft-alignment"
    assert map_telemetry_to_service("PRV-04", symptom="valve seat chatter") == "valve-integrity-test"


import uuid

def test_autonomous_trigger_from_telemetry():
    """Verify telemetry trigger automates Quote -> Policy -> Invoice -> Payment -> Graph (Section 16)."""
    test_evt_id = f"EVT-VIB-TEST-{uuid.uuid4().hex[:8]}"
    payload = {
        "equipment_tag": "P-101A",
        "event_id": test_evt_id,
        "failure_event_id": "FE-001",
        "confidence": 0.94,
        "work_order_id": "WO-2026-P101",
    }
    res1 = client.post("/api/machine-money/trigger-from-telemetry", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value)
    assert data1["amount_sats"] == 250
    assert data1["is_duplicate_prevented"] is False
    assert data1["payment_hash"] is not None
    assert data1["preimage"] is not None
    assert "FE-001" in data1["evidence_package"]["evidence"]

    # Test idempotency: re-triggering with identical event returns existing payment without double charging
    res2 = client.post("/api/machine-money/trigger-from-telemetry", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["payment_id"] == data1["payment_id"]
    assert data2["is_duplicate_prevented"] is True


def test_agent_tool_governed_boundary():
    """Verify Section 17 agent tool boundary: LLM proposes, policy engine authorizes."""
    # 1. Valid proposal within policy cap
    valid_proposal = {
        "action": "PAY_FOR_SERVICE",
        "service_id": "bearing-inspection",
        "equipment_tag": "P-101A",
        "reason": "Vibration excursion matches FE-001 historical bearing degradation signature",
        "evidence": ["FE-001", "WO-1002", "PROC-001"],
        "confidence": 0.95,
        "event_id": "EVT-AGENT-TOOL-001",
    }
    res = client.post("/api/machine-money/agent-tool", json=valid_proposal)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value)
    assert data["amount_sats"] == 250

    # 2. Invalid service proposed by agent -> Rejected by backend
    invalid_proposal = {
        "action": "PAY_FOR_SERVICE",
        "service_id": "unapproved-darknet-service",
        "equipment_tag": "P-101A",
    }
    bad_res = client.post("/api/machine-money/agent-tool", json=invalid_proposal)
    assert bad_res.status_code == 400


def test_evidence_retrieval_endpoint():
    """Verify GET /api/machine-money/evidence/{payment_id} returns cross-layer justification (Section 18)."""
    # 1. Execute a payment via telemetry trigger
    payload = {
        "equipment_tag": "P-101A",
        "event_id": "EVT-EVIDENCE-TEST",
        "confidence": 0.92,
    }
    trigger_res = client.post("/api/machine-money/trigger-from-telemetry", json=payload)
    payment_id = trigger_res.json()["payment_id"]

    # 2. Fetch evidence package
    ev_res = client.get(f"/api/machine-money/evidence/{payment_id}")
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert ev_data["payment_id"] == payment_id
    assert "evidence_package" in ev_data
    assert len(ev_data["evidence_package"]["evidence"]) >= 3
    assert "cross_layer_justification" in ev_data["evidence_package"]
