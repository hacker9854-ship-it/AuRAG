"""Unit and integration tests for Task 6.2: Enriched human approval evidence package."""
import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import hashlib
from backend.app.db.models import Base
from backend.app.main import app
from backend.app.services.machine_money.bolt11 import encode_bolt11
from backend.app.services.machine_money.schemas import (
    HumanApprovalEvidencePackage,
    PaymentStatus,
)
from backend.app.services.machine_money.service import MachineMoneyService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mm_service():
    return MachineMoneyService()


def test_human_approval_evidence_structure_and_api(client, mm_service):
    """Task 6.2: Complete context (telemetry, economics, procedure, policy) before human approval sign-off."""
    # 1. Trigger judge mode policy escalation (1200 sats > 500 sat cap)
    res = asyncio.run(
        mm_service.execute_judge_scenario(
            db=None,
            scenario="POLICY_ESCALATION",
            equipment_id="P-101A",
            override_cost_sats=1200,
            auto_approve=False,
        )
    )
    assert res.status == "PENDING_APPROVAL"
    pid = res.payment_record["payment_id"] if res.payment_record else None

    # 2. Query approval evidence via API
    # Since in-memory/test sessions might use default db, test service get_approval_evidence
    from backend.app.db.database import SessionLocal
    db = SessionLocal()
    try:
        # Create an escalation payment in db
        escalation_h = hashlib.sha256(b"escalation_invoice_1200").hexdigest()
        escalation_inv = encode_bolt11(network="bcrt", amount_sats=1200, payment_hash_hex=escalation_h, description="Escalation overhaul")
        payment = asyncio.run(
            mm_service.execute_payment(
                db=db,
                bolt11=escalation_inv,
                amount_sats=1200,
                vendor_name="Heavy Turbomachinery Overhaul Node",
                event_id="EVT-VIB-001",
                work_order_id="WO-2026-P101",
            )
        )
        assert payment.status == PaymentStatus.PENDING_APPROVAL.value

        evidence = mm_service.get_approval_evidence(db, payment.payment_id)
        assert isinstance(evidence, HumanApprovalEvidencePackage)

        # Asset & Equipment context
        assert evidence.equipment_id == "P-101A"
        assert "Charge Pump" in evidence.equipment_name

        # Policy & Cap analysis
        assert evidence.amount_sats == 1200
        assert evidence.autonomous_cap_sats == 500
        assert evidence.excess_sats_over_cap == 700
        assert evidence.confidence_percentage >= 85.0
        assert "exceeds autonomous threshold cap" in evidence.policy_reason

        # Operational Evidence & Procedure
        assert evidence.failure_event_id == "FE-001"
        assert evidence.governing_procedure == "PROC-001"
        assert evidence.telemetry_excursion["sensor"] == "vibration_radial_mms"
        assert evidence.telemetry_excursion["measured_value"] == 5.8
        assert evidence.telemetry_excursion["standard"] == "ISO 10816 Zone C"

        # Industrial Economics
        assert evidence.industrial_economics["downtime_hours_avoided"] == 4.5
        assert evidence.industrial_economics["gross_exposure_usd"] == 1170000.0

        # Actionable guidance
        assert len(evidence.recommended_action) > 10
        assert len(evidence.rollback_guidance) > 10

        # 3. Test API endpoint
        api_res = client.get(f"/api/machine-money/payments/{payment.payment_id}/approval-evidence")
        assert api_res.status_code == 200
        api_data = api_res.json()
        assert api_data["payment_id"] == payment.payment_id
        assert api_data["excess_sats_over_cap"] == 700
        assert api_data["governing_procedure"] == "PROC-001"
        assert api_data["failure_event_id"] == "FE-001"
        assert api_data["industrial_economics"]["gross_exposure_usd"] == 1170000.0
    finally:
        db.close()
