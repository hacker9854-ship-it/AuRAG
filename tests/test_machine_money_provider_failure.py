"""Unit tests for Machine Money Provider Failure and Unsettled Payment Scenario (Task 6.3)."""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import Base, PaymentRecord, AuditEvent
from backend.app.main import app
import hashlib
from backend.app.services.machine_money.bolt11 import encode_bolt11
from backend.app.services.machine_money.providers.mock import register_preimage
from backend.app.services.machine_money.schemas import (
    ExecutionStage,
    JudgeExecutionResponse,
    PaymentStatus,
)
from backend.app.services.machine_money.service import MachineMoneyService


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def service():
    return MachineMoneyService()


@pytest.fixture
def client():
    return TestClient(app)


def test_judge_mode_provider_failure_scenario(service, test_db):
    """Scenario C: Provider failure halts at settlement, marks status FAILED, leaves payment unsettled with retry guidance."""
    res = asyncio.run(
        service.execute_judge_scenario(
            db=test_db,
            scenario="PROVIDER_FAILURE",
            equipment_id="P-101A",
            override_cost_sats=250,
            auto_approve=True,
        )
    )

    assert isinstance(res, JudgeExecutionResponse)
    assert res.status == "FAILED"
    assert res.scenario == "PROVIDER_FAILURE"

    # Stages: ANOMALY_DETECTED through SETTLEMENT_CONFIRMED (FAILED), never links graph or resolves outcome
    stages = [e.stage for e in res.events]
    assert ExecutionStage.SETTLEMENT_CONFIRMED in stages
    assert ExecutionStage.GRAPH_LINKED not in stages
    assert ExecutionStage.OUTCOME_RESOLVED not in stages

    settlement_event = next(e for e in res.events if e.stage == ExecutionStage.SETTLEMENT_CONFIRMED)
    assert settlement_event.status == "FAILED"
    assert "Channel route liquidity exhausted" in settlement_event.message
    assert settlement_event.data["settled"] is False
    assert "retry_guidance" in settlement_event.data

    # Payment record verification
    assert res.payment_record is not None
    assert res.payment_record["status"] == "FAILED"
    assert res.payment_record["amount_sats"] == 250
    assert "Re-balance payment channel via LSP" in res.payment_record["retry_guidance"]

    # Audit event verification in DB
    audit = (
        test_db.query(AuditEvent)
        .filter(
            AuditEvent.action_type == "PAYMENT_SETTLEMENT_FAILED",
            AuditEvent.resource_id == res.payment_record["payment_id"],
        )
        .first()
    )
    assert audit is not None
    assert audit.status == "FAILED"
    details = json.loads(audit.details_json)
    assert details["error_code"] == "PROVIDER_PAY_FAILED"
    assert "retry_guidance" in details
    assert details["amount_sats"] == 250


def test_execute_payment_records_failure_and_retry_guidance(service, test_db, monkeypatch):
    """Direct payment execution failure triggers audit recording and leaves payment unsettled."""
    # Mock provider pay_invoice safely with monkeypatch so other tests are not affected
    monkeypatch.setattr(
        service.provider,
        "pay_invoice",
        AsyncMock(side_effect=Exception("TEMPORARY_CHANNEL_FAILURE: Insufficient capacity")),
    )

    bolt11_mock = "lnbc2500n1mockfailinvoice0000000000000000000000000000000000000000000000000"
    record = asyncio.run(
        service.execute_payment(
            db=test_db,
            bolt11=bolt11_mock,
            amount_sats=250,
            work_order_id="WO-FAIL-01",
            event_id="EVT-FAIL-01",
            idempotency_key="idemp-fail-test-01",
        )
    )

    assert record.status == PaymentStatus.FAILED.value
    assert record.error_code == "PROVIDER_PAY_FAILED"
    assert "Insufficient capacity" in record.error_message
    assert record.paid_at is None
    assert record.preimage is None

    # Verify AuditEvent
    audit = (
        test_db.query(AuditEvent)
        .filter(
            AuditEvent.action_type == "PAYMENT_SETTLEMENT_FAILED",
            AuditEvent.resource_id == record.payment_id,
        )
        .first()
    )
    assert audit is not None
    assert audit.status == "FAILED"
    details = json.loads(audit.details_json)
    assert "Zero satoshis deducted" in details["retry_guidance"]


def test_judge_mode_provider_failure_api_endpoint(client):
    """POST /api/machine-money/judge/execute with PROVIDER_FAILURE returns FAILED execution response."""
    response = client.post(
        "/api/machine-money/judge/execute",
        json={"scenario": "PROVIDER_FAILURE", "equipment_id": "P-101A", "override_cost_sats": 250},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "FAILED"
    assert data["scenario"] == "PROVIDER_FAILURE"
    assert data["payment_record"]["status"] == "FAILED"
    assert "retry_guidance" in data["payment_record"]
    assert "Channel route liquidity exhausted" in data["events"][-1]["message"]


# -----------------------------------------------------------------------------
# Phase 1: Machine Money Service & Provider Rejection Tests
# -----------------------------------------------------------------------------

def test_execute_payment_rejects_unregistered_invoice_zero_sats_lost(service, test_db):
    """Phase 1.2 & 1.4: Service attempting to pay an unregistered invoice records FAILED, 0 sats lost."""
    initial_balance = service.provider.balance_sats
    unregistered_hash = hashlib.sha256(b"unregistered_payment_hash_test_service").hexdigest()
    unreg_bolt11 = encode_bolt11(
        network="bcrt",
        amount_sats=250,
        payment_hash_hex=unregistered_hash,
        description="Unregistered service test",
    )

    record = asyncio.run(
        service.execute_payment(
            db=test_db,
            bolt11=unreg_bolt11,
            amount_sats=250,
            work_order_id="WO-UNREG-01",
            event_id="EVT-UNREG-01",
            idempotency_key="idemp-unreg-01",
        )
    )

    assert record.status == PaymentStatus.FAILED.value
    assert record.error_code == "PROVIDER_PAY_FAILED"
    assert "unregistered" in record.error_message.lower()
    assert record.preimage is None
    assert record.paid_at is None
    assert service.provider.balance_sats == initial_balance

    # Verify audit event
    audit = (
        test_db.query(AuditEvent)
        .filter(
            AuditEvent.action_type == "PAYMENT_SETTLEMENT_FAILED",
            AuditEvent.resource_id == record.payment_id,
        )
        .first()
    )
    assert audit is not None
    assert audit.status == "FAILED"
    details = json.loads(audit.details_json)
    assert "Zero satoshis deducted" in details["retry_guidance"]


def test_execute_payment_rejects_malformed_invoice_zero_sats_lost(service, test_db):
    """Phase 1.1: Service attempting to pay malformed invoice string records FAILED, 0 sats lost."""
    initial_balance = service.provider.balance_sats
    malformed_bolt11 = "lnbcrt_totally_invalid_data"

    record = asyncio.run(
        service.execute_payment(
            db=test_db,
            bolt11=malformed_bolt11,
            amount_sats=250,
            work_order_id="WO-MALFORM-01",
            event_id="EVT-MALFORM-01",
            idempotency_key="idemp-malform-01",
        )
    )

    assert record.status == PaymentStatus.FAILED.value
    assert record.error_code == "PROVIDER_PAY_FAILED"
    assert record.preimage is None
    assert service.provider.balance_sats == initial_balance


def test_execute_payment_rejects_mismatched_preimage_zero_sats_lost(service, test_db):
    """Phase 1.3: Service attempting to pay with mismatched preimage records FAILED, 0 sats lost."""
    initial_balance = service.provider.balance_sats
    test_hash = hashlib.sha256(b"preimage_mismatch_service_test").hexdigest()
    register_preimage(test_hash, "ee" * 32)  # Bogus preimage

    mismatch_bolt11 = encode_bolt11(
        network="bcrt",
        amount_sats=250,
        payment_hash_hex=test_hash,
        description="Mismatched proof test",
    )

    record = asyncio.run(
        service.execute_payment(
            db=test_db,
            bolt11=mismatch_bolt11,
            amount_sats=250,
            work_order_id="WO-MISMATCH-01",
            event_id="EVT-MISMATCH-01",
            idempotency_key="idemp-mismatch-01",
        )
    )

    assert record.status == PaymentStatus.FAILED.value
    assert record.error_code == "PROVIDER_PAY_FAILED"
    assert "mismatch" in record.error_message.lower() or "proof" in record.error_message.lower()
    assert record.preimage is None
    assert service.provider.balance_sats == initial_balance
