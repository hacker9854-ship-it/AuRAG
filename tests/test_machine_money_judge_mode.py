"""Tests for Machine Money Judge Mode Orchestrator and Structured Execution Events (Phase 2)."""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.machine_money.schemas import (
    ExecutionStage,
    JudgeExecutionRequest,
    JudgeExecutionResponse,
)
from backend.app.services.machine_money.service import MachineMoneyService


@pytest.fixture
def service():
    return MachineMoneyService()


@pytest.fixture
def client():
    return TestClient(app)


import asyncio


def test_judge_mode_industrial_emergency_lifecycle(service):
    """Scenario A: Autonomous Industrial Emergency demo executes all 9 stages with measured timings."""
    res = asyncio.run(
        service.execute_judge_scenario(
            db=None,
            scenario="INDUSTRIAL_EMERGENCY",
            equipment_id="P-101A",
            override_cost_sats=250,
            auto_approve=True,
        )
    )

    assert isinstance(res, JudgeExecutionResponse)
    assert res.status == "SUCCESS"
    assert res.scenario == "INDUSTRIAL_EMERGENCY"
    assert res.total_elapsed_ms >= 0
    assert len(res.events) == 9

    # Verify each expected stage in chronological order
    expected_stages = [
        ExecutionStage.ANOMALY_DETECTED,
        ExecutionStage.EVIDENCE_MATCHED,
        ExecutionStage.QUOTE_RESOLVED,
        ExecutionStage.POLICY_EVALUATED,
        ExecutionStage.INVOICE_GENERATED,
        ExecutionStage.PAYMENT_AUTHORIZED,
        ExecutionStage.SETTLEMENT_CONFIRMED,
        ExecutionStage.GRAPH_LINKED,
        ExecutionStage.OUTCOME_RESOLVED,
    ]
    actual_stages = [e.stage for e in res.events]
    assert actual_stages == expected_stages

    # Verify stage properties
    for event in res.events:
        assert event.status == "SUCCESS"
        assert event.elapsed_ms >= 0
        assert len(event.message) > 0

    # Payment record verification
    assert res.payment_record is not None
    assert res.payment_record["amount_sats"] == 250
    assert res.payment_record["status"] == "SETTLED"
    assert res.payment_record["payment_hash"] is not None
    assert res.payment_record["preimage"] is not None


def test_judge_mode_policy_escalation_lifecycle(service):
    """Scenario B: High amount (> 500 sats) halts at policy gate and routes to human operator review."""
    res = asyncio.run(
        service.execute_judge_scenario(
            db=None,
            scenario="POLICY_ESCALATION",
            equipment_id="P-101A",
            override_cost_sats=1200,  # Exceeds 500 sats cap
            auto_approve=True,
        )
    )

    assert res.status == "PENDING_APPROVAL"
    assert res.payment_record["amount_sats"] == 1200
    assert res.payment_record["status"] == "PENDING_APPROVAL"

    # Should stop at POLICY_EVALUATED
    stages = [e.stage for e in res.events]
    assert ExecutionStage.POLICY_EVALUATED in stages
    assert ExecutionStage.SETTLEMENT_CONFIRMED not in stages

    policy_event = next(e for e in res.events if e.stage == ExecutionStage.POLICY_EVALUATED)
    assert policy_event.status == "PENDING_APPROVAL"
    assert "exceeds autonomous cap" in policy_event.message.lower()


def test_judge_mode_api_endpoint(client):
    """Verify POST /api/machine-money/judge/execute and /judge/reset HTTP endpoints."""
    # 1. Execute
    response = client.post(
        "/api/machine-money/judge/execute",
        json={"scenario": "INDUSTRIAL_EMERGENCY", "equipment_id": "P-101A", "override_cost_sats": 250},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert len(data["events"]) == 9
    assert "EXEC-JM-" in data["execution_id"]

    # 2. Reset
    reset_resp = client.post("/api/machine-money/judge/reset")
    assert reset_resp.status_code == 200
    reset_data = reset_resp.json()
    assert reset_data["status"] == "RESET"
    assert reset_data["ready"] is True
