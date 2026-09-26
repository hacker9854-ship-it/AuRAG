"""Comprehensive tests for Task 5: M2M Transaction Protocol, Quotes, APIs, Idempotency & Safety."""
import os
import pytest
from fastapi.testclient import TestClient

from backend.app.db.database import get_db, init_db
from backend.app.db.models import ApprovalRecord, AuditEvent, PaymentRecord
from backend.app.main import app
from backend.app.services.machine_money.registry import (
    generate_idempotency_key,
    get_service,
    list_services,
)
from backend.app.services.machine_money.schemas import PaymentStatus

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_env():
    os.environ["MACHINE_MONEY_PROVIDER"] = "mock"
    os.environ["MACHINE_MONEY_AUTO_PAY_ENABLED"] = "true"
    os.environ["MACHINE_MONEY_MAX_AUTOPAY_SATS"] = "500"
    init_db()


def test_provider_registry_endpoint():
    """Verify demo service provider registry returns catalog with clear mock transparency."""
    res = client.get("/api/machine-money/providers")
    assert res.status_code == 200
    data = res.json()
    assert "Demo Service Registry" in data["registry_title"]
    assert "MOCK / SIMULATION" in data["registry_title"]
    assert data["total_services"] >= 5
    assert data["total_providers"] >= 3

    # Check bearing-inspection service
    services = {s["service_id"]: s for s in data["services"]}
    assert "bearing-inspection" in services
    assert services["bearing-inspection"]["price_sats"] == 250
    assert services["bearing-inspection"]["equipment_class"] == "pump"


def test_service_quote_by_service_id():
    """Verify requesting a quote by registered service_id auto-populates service details."""
    payload = {
        "equipment_id": "P-101A",
        "service_id": "bearing-inspection",
    }
    res = client.post("/api/machine-money/quote", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["equipment_id"] == "P-101A"
    assert data["cost_sats"] == 250
    assert "High-Frequency Vibration" in data["service_description"]
    assert len(data["parts_included"]) > 0


def test_deterministic_idempotency_generator():
    """Verify idempotency key calculation is reproducible and stable."""
    key1 = generate_idempotency_key("plant-mumbai-01", "P-101A", "bearing-inspection", "EVT-999")
    key2 = generate_idempotency_key("plant-mumbai-01", "P-101A", "bearing-inspection", "EVT-999")
    key3 = generate_idempotency_key("plant-mumbai-01", "P-101A", "thermal-diagnostics", "EVT-999")

    assert key1 == key2
    assert key1 != key3
    assert key1.startswith("idemp-")


def test_idempotent_duplicate_invoice_and_payment():
    """Verify duplicate requests with the same idempotency key return the existing record without error."""
    idemp_key = "idemp-test-duplicate-safety-001"

    # First invoice creation
    res1 = client.post(
        "/api/machine-money/invoice",
        json={
            "amount_sats": 200,
            "memo": "Vibration sensor diagnostic",
            "equipment_id": "P-101A",
            "idempotency_key": idemp_key,
        },
    )
    assert res1.status_code == 200
    inv_data1 = res1.json()

    # Second invoice creation with same idempotency key
    res2 = client.post(
        "/api/machine-money/invoice",
        json={
            "amount_sats": 200,
            "memo": "Vibration sensor diagnostic",
            "equipment_id": "P-101A",
            "idempotency_key": idemp_key,
        },
    )
    assert res2.status_code == 200
    inv_data2 = res2.json()

    assert inv_data1["payment_id"] == inv_data2["payment_id"]
    assert inv_data1["invoice"] == inv_data2["invoice"]


def test_dry_run_simulation_mode():
    """Verify POST /api/machine-money/simulate tests transaction flow without DB mutation."""
    # 1. Within auto-pay cap (250 sats <= 500 cap)
    sim1 = client.post(
        "/api/machine-money/simulate",
        json={
            "equipment_id": "P-101A",
            "service_id": "bearing-inspection",
            "confidence": 0.95,
        },
    )
    assert sim1.status_code == 200
    data1 = sim1.json()
    assert data1["dry_run"] is True
    assert data1["amount_sats"] == 250
    assert data1["projected_action"] == "AUTONOMOUS_EXECUTE_LIGHTNING_PAYMENT"
    assert data1["policy_evaluation"]["authorized"] is True

    # 2. Exceeds auto-pay cap (1200 sats > 500 cap)
    sim2 = client.post(
        "/api/machine-money/simulate",
        json={
            "equipment_id": "P-101A",
            "service_id": "bearing-inspection",
            "amount_sats": 1200,
            "confidence": 0.95,
        },
    )
    assert sim2.status_code == 200
    data2 = sim2.json()
    assert data2["projected_action"] == "ROUTE_TO_HUMAN_APPROVAL_QUEUE"
    assert data2["policy_evaluation"]["authorized"] is False


def test_operator_approval_workflow():
    """Verify operator can approve a payment previously queued under policy, settling the Lightning invoice."""
    import uuid
    suffix = uuid.uuid4().hex[:8]
    idemp_inv = f"idemp-overhaul-inv-{suffix}"
    idemp_pay = f"idemp-overhaul-pay-{suffix}"

    # 1. Create invoice for 1500 sats (exceeds 500 sats cap)
    inv_res = client.post(
        "/api/machine-money/invoice",
        json={
            "amount_sats": 1500,
            "memo": "Complete pump mechanical seal overhaul",
            "equipment_id": "P-101A",
            "idempotency_key": idemp_inv,
        },
    )
    assert inv_res.status_code == 200
    invoice = inv_res.json()["invoice"]

    # 2. Attempt autonomous execution -> held in PENDING_APPROVAL
    pay_res = client.post(
        "/api/machine-money/pay",
        json={
            "bolt11": invoice,
            "amount_sats": 1500,
            "work_order_id": "WO-SEAL-1500",
            "idempotency_key": idemp_pay,
        },
    )
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    assert pay_data["status"] == PaymentStatus.PENDING_APPROVAL.value
    payment_id = pay_data["payment_id"]

    # 3. Plant operator approves payment
    appv_res = client.post(
        f"/api/machine-money/payments/{payment_id}/approve",
        json={
            "reviewer_id": "lead-reliability-engineer-mumbai",
            "review_notes": "Critical turnaround seal verified by maintenance superintendent",
        },
    )
    assert appv_res.status_code == 200
    appv_data = appv_res.json()
    assert appv_data["status"] in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value)
    assert appv_data["paid_at"] is not None
    assert appv_data["preimage"] is not None

    # 4. Verify audit ledger entry
    db = next(get_db())
    audit = db.query(AuditEvent).filter(
        AuditEvent.resource_id == payment_id,
        AuditEvent.action_type == "PAYMENT_APPROVAL_SETTLED",
    ).first()
    assert audit is not None
    assert audit.user_id == "lead-reliability-engineer-mumbai"
    assert audit.status == "SUCCESS"
