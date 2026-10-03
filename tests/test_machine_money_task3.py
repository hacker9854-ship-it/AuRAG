"""Comprehensive tests for Task 3: Payment Provider Abstraction, Domain Models, and APIs."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import get_db, init_db
from backend.app.db.models import PaymentRecord, ApprovalRecord, AuditEvent

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure tables exist before tests run and mock provider is active."""
    import os
    os.environ["MACHINE_MONEY_PROVIDER"] = "mock"
    os.environ["MACHINE_MONEY_NETWORK"] = "regtest"
    init_db()


def test_machine_money_health():
    """Verify health endpoint reports connected mock provider."""
    res = client.get("/api/machine-money/health")
    assert res.status_code == 200
    data = res.json()
    assert data["is_connected"] is True
    assert data["provider_name"] == "mock"
    assert data["network"] == "regtest"
    assert data["balance_sats"] > 0


def test_service_quotation():
    """Verify service quote generation."""
    payload = {
        "equipment_id": "P-101A",
        "service_description": "Bearing vibration corrective overhaul",
        "cost_sats": 200,
    }
    res = client.post("/api/machine-money/quote", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["equipment_id"] == "P-101A"
    assert data["cost_sats"] == 200
    assert "quote_id" in data
    assert len(data["parts_included"]) > 0


def test_invoice_creation():
    """Verify BOLT11 invoice generation and database persistence."""
    payload = {
        "amount_sats": 150,
        "memo": "Bearing replacement for Pump P-101A",
        "work_order_id": "WO-2026-P101",
        "equipment_id": "P-101A",
    }
    res = client.post("/api/machine-money/invoice", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "INVOICE_CREATED"
    assert data["amount_sats"] == 150
    assert data["invoice"].startswith("lnbcrt150")
    assert data["work_order_id"] == "WO-2026-P101"
    assert "payment_id" in data


def test_autonomous_payment_execution():
    """Verify payment execution with policy bypass (simulating authorized auto-pay)."""
    # 1. Create invoice
    inv_res = client.post("/api/machine-money/invoice", json={
        "amount_sats": 100,
        "memo": "Sensor calibration fee",
        "work_order_id": "WO-AUTO-01",
    })
    invoice = inv_res.json()["invoice"]

    # 2. Pay invoice
    pay_payload = {
        "bolt11": invoice,
        "amount_sats": 100,
        "work_order_id": "WO-AUTO-01",
        "idempotency_key": "idemp-test-001",
        "bypass_policy": True,
    }
    pay_res = client.post("/api/machine-money/pay", json=pay_payload)
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    assert pay_data["status"] == "MOCK_PAID"
    assert pay_data["preimage"] is not None
    assert pay_data["payment_hash"] is not None

    # 3. Test idempotency — repeat payment with same key
    repeat_res = client.post("/api/machine-money/pay", json=pay_payload)
    assert repeat_res.status_code == 200
    assert repeat_res.json()["payment_id"] == pay_data["payment_id"]


def test_spending_limit_policy_guard():
    """Verify that transactions exceeding autonomous policy threshold are routed to human approval."""
    # Invoice for 5,000 sats (exceeds default limit of 500 sats)
    inv_res = client.post("/api/machine-money/invoice", json={
        "amount_sats": 5000,
        "memo": "Expensive full impeller replacement",
        "work_order_id": "WO-HIGH-VALUE",
    })
    invoice = inv_res.json()["invoice"]

    pay_payload = {
        "bolt11": invoice,
        "amount_sats": 5000,
        "work_order_id": "WO-HIGH-VALUE",
        "idempotency_key": "idemp-high-value-002",
        "bypass_policy": False,  # Strict policy enforcement
    }
    pay_res = client.post("/api/machine-money/pay", json=pay_payload)
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    assert pay_data["status"] == "PENDING_APPROVAL"
    assert pay_data["approval_id"] is not None


def test_payment_history_listing():
    """Verify that recent payments can be retrieved chronologically."""
    res = client.get("/api/machine-money/payments")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 2
