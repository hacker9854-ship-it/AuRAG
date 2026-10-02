"""Unit tests for Machine Money Idempotency and Duplicate Trigger Handling (Task 6.4 & FR-12).

Proves that repeat triggers for the same logical event, service, and equipment
do not result in duplicate Lightning settlements or duplicate charges.
"""
import asyncio
import uuid
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import Base, PaymentRecord, ApprovalRecord
from backend.app.main import app
from backend.app.services.machine_money.registry import generate_idempotency_key
import hashlib
from backend.app.services.machine_money.bolt11 import encode_bolt11
from backend.app.services.machine_money.schemas import (
    InvoiceRequest,
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


def test_telemetry_trigger_duplicate_prevention_settled(client):
    """Scenario D: Re-sending the same logical trigger prevents duplicate settlement and returns same idempotency key."""
    unique_event_id = f"EVT-IDEMP-TEST-{uuid.uuid4().hex[:8]}"
    payload = {
        "equipment_tag": "P-101A",
        "event_id": unique_event_id,
        "failure_event_id": "FE-001",
        "confidence": 0.94,
        "work_order_id": "WO-IDEMP-001",
    }

    # 1. Initial Trigger: Executes Quote -> Policy -> Invoice -> Settlement
    res1 = client.post("/api/machine-money/trigger-from-telemetry", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value)
    assert data1["is_duplicate_prevented"] is False
    idempotency_key = data1["idempotency_key"]
    payment_id = data1["payment_id"]
    assert idempotency_key.startswith("idemp-")

    # 2. Duplicate Trigger: Re-sending the exact same event
    res2 = client.post("/api/machine-money/trigger-from-telemetry", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()

    # Verify duplicate guard behavior
    assert data2["is_duplicate_prevented"] is True
    assert data2["idempotency_key"] == idempotency_key
    assert data2["payment_id"] == payment_id
    assert data2["status"] == data1["status"]
    assert data2["amount_sats"] == data1["amount_sats"]
    assert data2["payment_hash"] == data1["payment_hash"]
    assert data2["preimage"] == data1["preimage"]


def test_telemetry_trigger_duplicate_prevention_pending_approval(client):
    """Duplicate trigger for a payment in PENDING_APPROVAL preserves the record and prevents duplicate approvals."""
    unique_event_id = f"EVT-ESC-IDEMP-{uuid.uuid4().hex[:8]}"
    # Using a turbine which maps to laser-shaft-alignment (400 sats) or custom override
    payload = {
        "equipment_tag": "TURBINE-01",
        "event_id": unique_event_id,
        "failure_event_id": "FE-001",
        "confidence": 0.50,  # Below confidence threshold -> routes to PENDING_APPROVAL
        "work_order_id": "WO-ESC-IDEMP-01",
    }

    # 1. First Trigger: Queues in PENDING_APPROVAL
    res1 = client.post("/api/machine-money/trigger-from-telemetry", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == PaymentStatus.PENDING_APPROVAL.value
    assert data1["is_duplicate_prevented"] is False
    idemp_key = data1["idempotency_key"]
    pid = data1["payment_id"]

    # 2. Second Trigger: Identical trigger must not generate a new approval or payment record
    res2 = client.post("/api/machine-money/trigger-from-telemetry", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["is_duplicate_prevented"] is True
    assert data2["idempotency_key"] == idemp_key
    assert data2["payment_id"] == pid
    assert data2["status"] == PaymentStatus.PENDING_APPROVAL.value


def test_service_execute_payment_idempotency(service, test_db, monkeypatch):
    """Direct execute_payment with identical idempotency_key executes provider settlement only once."""
    pay_spy = AsyncMock(wraps=service.provider.pay_invoice)
    monkeypatch.setattr(service.provider, "pay_invoice", pay_spy)

    idemp_key = f"idemp-direct-test-{uuid.uuid4().hex[:8]}"
    idemp_h = hashlib.sha256(b"idemp_test_invoice_250").hexdigest()
    bolt11 = encode_bolt11(network="bcrt", amount_sats=250, payment_hash_hex=idemp_h, description="Idempotency test service")

    # Call 1
    rec1 = asyncio.run(
        service.execute_payment(
            db=test_db,
            bolt11=bolt11,
            amount_sats=250,
            work_order_id="WO-DIR-01",
            idempotency_key=idemp_key,
        )
    )
    assert rec1.status in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value)
    assert pay_spy.call_count == 1

    # Call 2 with identical idempotency_key
    rec2 = asyncio.run(
        service.execute_payment(
            db=test_db,
            bolt11=bolt11,
            amount_sats=250,
            work_order_id="WO-DIR-01",
            idempotency_key=idemp_key,
        )
    )
    assert rec2.payment_id == rec1.payment_id
    assert rec2.status == rec1.status
    # Provider pay_invoice must NOT be called again (zero duplicate charges)
    assert pay_spy.call_count == 1

    # Exactly 1 record in DB
    records_count = test_db.query(PaymentRecord).filter(PaymentRecord.idempotency_key == idemp_key).count()
    assert records_count == 1


def test_create_invoice_idempotency(service, test_db):
    """create_invoice returns existing invoice record when idempotency_key is reused."""
    idemp_key = f"idemp-inv-test-{uuid.uuid4().hex[:8]}"
    req = InvoiceRequest(
        amount_sats=300,
        memo="Bearing oil inspection",
        equipment_id="P-101A",
        idempotency_key=idemp_key,
    )

    inv1 = asyncio.run(service.create_invoice(test_db, req))
    inv2 = asyncio.run(service.create_invoice(test_db, req))

    assert inv1.payment_id == inv2.payment_id
    assert inv1.invoice == inv2.invoice
    assert test_db.query(PaymentRecord).filter(PaymentRecord.idempotency_key == idemp_key).count() == 1


def test_judge_mode_idempotency_key_visibility(service):
    """Judge Mode execution returns visible, deterministic idempotency key in payment_record."""
    res = asyncio.run(
        service.execute_judge_scenario(
            db=None,
            scenario="INDUSTRIAL_EMERGENCY",
            equipment_id="P-101A",
            override_cost_sats=250,
        )
    )
    assert res.payment_record is not None
    assert "idempotency_key" in res.payment_record
    assert res.payment_record["idempotency_key"].startswith("idemp-")

    # Verify Stage 6 also references the same idempotency key
    auth_event = next(e for e in res.events if e.stage.value == "PAYMENT_AUTHORIZED")
    assert auth_event.data["idempotency_key"] == res.payment_record["idempotency_key"]
