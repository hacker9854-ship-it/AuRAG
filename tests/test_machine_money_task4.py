"""Tests for Task 4: Neo4j Knowledge Graph integration & Automation Policy Governance."""
import os
import pytest
from fastapi.testclient import TestClient

from backend.app.core.neo4j import FallbackNeo4jSession
from backend.app.db.database import get_db, init_db
from backend.app.db.models import ApprovalRecord, AuditEvent, AutomationPolicy, PaymentRecord
from backend.app.main import app
from backend.app.services.automation import (
    evaluate_automation_trigger,
    evaluate_lightning_payment_policy,
    seed_default_policies_if_empty,
)
from backend.app.services.machine_money.graph import (
    get_payment_graph_trail,
    record_payment_in_graph,
)
from backend.app.services.machine_money.schemas import PaymentStatus
from backend.app.services.machine_money.service import MachineMoneyService


@pytest.fixture(autouse=True)
def setup_env():
    os.environ["MACHINE_MONEY_PROVIDER"] = "mock"
    os.environ["MACHINE_MONEY_AUTO_PAY_ENABLED"] = "true"
    os.environ["MACHINE_MONEY_MAX_AUTOPAY_SATS"] = "500"
    init_db()


def test_seed_and_lightning_policy():
    """Verify POL-LIGHTNING-MACHINE-MONEY is seeded with correct parameters."""
    db = next(get_db())
    seed_default_policies_if_empty(db)

    policy = (
        db.query(AutomationPolicy)
        .filter(AutomationPolicy.policy_id == "POL-LIGHTNING-MACHINE-MONEY")
        .first()
    )
    assert policy is not None
    assert policy.action_type == "PAY_LIGHTNING_INVOICE"
    assert policy.target_system == "LIGHTNING"
    assert policy.trigger_type == "PREDICTIVE_RISK_HIGH"


def test_evaluate_lightning_payment_policy_rules():
    """Test policy gating under different limits, confidence scores, and autopay states."""
    db = next(get_db())

    # 1. Within limit and high confidence -> Authorized
    eval1 = evaluate_lightning_payment_policy(
        db, amount_sats=250, confidence=0.92, autopay_enabled=True, max_cap=500
    )
    assert eval1["authorized"] is True
    assert eval1["requires_approval"] is False

    # 2. Exceeds limit -> Requires Approval
    eval2 = evaluate_lightning_payment_policy(
        db, amount_sats=1200, confidence=0.95, autopay_enabled=True, max_cap=500
    )
    assert eval2["authorized"] is False
    assert eval2["requires_approval"] is True
    assert "exceeds autonomous threshold cap" in eval2["reason"]

    # 3. Low diagnostic confidence -> Requires Approval
    eval3 = evaluate_lightning_payment_policy(
        db, amount_sats=200, confidence=0.65, autopay_enabled=True, max_cap=500
    )
    assert eval3["authorized"] is False
    assert eval3["requires_approval"] is True
    assert "below the required policy threshold" in eval3["reason"]

    # 4. Autopay disabled -> Requires Approval
    eval4 = evaluate_lightning_payment_policy(
        db, amount_sats=100, confidence=0.99, autopay_enabled=False, max_cap=500
    )
    assert eval4["authorized"] is False
    assert eval4["requires_approval"] is True


def test_neo4j_graph_persistence_and_trail():
    """Test graph traversal answering 'Why was this payment made?'."""
    session = FallbackNeo4jSession()

    # Record payment
    ok = record_payment_in_graph(
        session=session,
        payment_id="PAY-TEST-TASK4",
        payment_hash="4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b",
        preimage="1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
        amount_sats=150,
        provider="mock",
        status="SETTLED",
        work_order_id="WO-2026-P101",
        predictive_event_id="EVT-VIB-001",
        service_provider_name="Industrial Dynamics Specialist Node",
    )
    assert ok is True

    # Retrieve graph trail
    trail = get_payment_graph_trail(session, "PAY-TEST-TASK4")
    assert trail["found"] is True
    assert trail["payment_id"] == "PAY-TEST-TASK4"
    assert trail["amount_sats"] == 150
    assert trail["work_order"]["id"] == "WO-2026-P101"
    assert trail["predictive_trigger"]["event_id"] == "EVT-VIB-001"
    assert trail["equipment"]["tag_id"] == "P-101A"
    assert len(trail["graph_story"]) == 5


def test_payment_trail_api_endpoint():
    """Test GET /api/machine-money/payments/{payment_id}/trail endpoint."""
    client = TestClient(app)
    response = client.get("/api/machine-money/payments/PAY-DEMO-001/trail")
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is True
    assert "graph_story" in data
    assert "work_order" in data
    assert "predictive_trigger" in data


def test_payment_policy_rejection_queues_approval():
    """Test that paying an invoice over the limit creates an ApprovalRecord and PENDING_APPROVAL status."""
    client = TestClient(app)

    # 1. Create invoice for 800 sats (> 500 cap)
    inv_res = client.post(
        "/api/machine-money/invoice",
        json={
            "amount_sats": 800,
            "memo": "Large pump overhaul parts",
            "equipment_id": "P-101A",
        },
    )
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    bolt11 = inv_data["invoice"]

    # 2. Attempt to pay without bypass
    pay_res = client.post(
        "/api/machine-money/pay",
        json={
            "bolt11": bolt11,
            "amount_sats": 800,
            "work_order_id": "WO-2026-P101",
        },
    )
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    assert pay_data["status"] == PaymentStatus.PENDING_APPROVAL.value
    assert pay_data["approval_id"] is not None

    # Check approval in database
    db = next(get_db())
    approval = db.query(ApprovalRecord).filter(ApprovalRecord.approval_id == pay_data["approval_id"]).first()
    assert approval is not None
    assert approval.target_system == "MACHINE_MONEY_LIGHTNING"
    assert approval.status == "PENDING"
