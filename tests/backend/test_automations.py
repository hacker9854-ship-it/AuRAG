"""Automated tests for enterprise automation engine, dry-run simulation, and approval workflows."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from backend.app.db.database import Base, get_db
from backend.app.db.models import ApprovalRecord, AuditEvent, AutomationPolicy, EvaluationRemediation
from backend.app.main import app
from backend.app.services.automation import (
    create_or_update_policy,
    evaluate_automation_trigger,
    list_automation_policies,
    list_pending_approvals,
    review_approval,
    seed_default_policies_if_empty,
)
from backend.app.services.evaluations import (
    create_remediation,
    list_remediations,
    update_remediation_status,
)


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def test_automation_policies_seeding_and_upsert(test_db):
    seed_default_policies_if_empty(test_db)
    policies = list_automation_policies(test_db)
    assert len(policies) >= 3

    policy_ids = [p["policy_id"] for p in policies]
    assert "POL-SAP-PM-CRITICAL" in policy_ids
    assert "POL-QMS-STATUTORY" in policy_ids
    assert "POL-PI-VIBRATION" in policy_ids

    # Create custom policy
    custom = create_or_update_policy(
        test_db,
        {
            "policy_id": "POL-CUSTOM-TEST",
            "name": "Custom Test Policy",
            "trigger_type": "BEARING_TEMP_HIGH",
            "action_type": "CREATE_SAP_WORK_ORDER",
            "target_system": "SAP_PM",
            "approval_threshold": "REQUIRES_APPROVAL",
            "parameters": {"temp_threshold_c": 85},
            "rollback_guidance": "Cancel work order via SAP PM IW32",
        },
        user_id="lead-engineer-01",
    )
    assert custom["policy_id"] == "POL-CUSTOM-TEST"

    # Verify audit event was logged
    audit = test_db.query(AuditEvent).filter(AuditEvent.resource_id == "POL-CUSTOM-TEST").first()
    assert audit is not None
    assert audit.action_type == "AUTOMATION_POLICY_CREATED"


def test_dry_run_simulation_does_not_mutate_database(test_db):
    seed_default_policies_if_empty(test_db)
    initial_approvals = test_db.query(ApprovalRecord).count()
    initial_audits = test_db.query(AuditEvent).count()

    context = {
        "equipment_tag": "P-101A",
        "health_index": 32,  # < 40 threshold
        "reason": "Bearing high vibration & cavitation detected",
    }

    result = evaluate_automation_trigger(
        db=test_db,
        trigger_type="HEALTH_INDEX_CRITICAL",
        site_id="plant-mumbai-01",
        context_data=context,
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert result["triggered_count"] >= 1

    action = result["actions"][0]
    assert action["status"] == "SIMULATED_PENDING_APPROVAL"
    assert action["target_system"] == "SAP_PM"
    assert "P-101A" in action["payload"]["title"]
    assert "Rollback" in action["rollback_guidance"]

    # Assert no records were committed
    assert test_db.query(ApprovalRecord).count() == initial_approvals
    assert test_db.query(AuditEvent).count() == initial_audits


def test_requires_approval_flow_and_review(test_db):
    seed_default_policies_if_empty(test_db)

    context = {
        "equipment_tag": "TK-301",
        "health_index": 25,
        "reason": "Internal corrosion risk threshold breached",
    }

    result = evaluate_automation_trigger(
        db=test_db,
        trigger_type="HEALTH_INDEX_CRITICAL",
        site_id="plant-mumbai-01",
        context_data=context,
        user_id="operator-01",
        dry_run=False,
    )

    assert result["dry_run"] is False
    assert result["triggered_count"] >= 1
    action = result["actions"][0]
    assert action["status"] == "QUEUED_FOR_APPROVAL"
    approval_id = action["approval_id"]

    # Verify pending queue
    pending = list_pending_approvals(test_db, site_id="plant-mumbai-01", status="PENDING")
    assert any(p["approval_id"] == approval_id for p in pending)

    # Approve action
    reviewed = review_approval(
        test_db,
        approval_id=approval_id,
        action="APPROVED",
        reviewed_by="plant-manager-01",
        review_notes="Approved for shutdown turnaround window",
    )
    assert reviewed["status"] == "APPROVED"
    assert reviewed["reviewed_by"] == "plant-manager-01"

    # Audit log verification
    audit = test_db.query(AuditEvent).filter(AuditEvent.resource_id == approval_id, AuditEvent.action_type == "APPROVAL_APPROVED").first()
    assert audit is not None


def test_autonomous_execution_flow(test_db):
    seed_default_policies_if_empty(test_db)

    context = {
        "equipment_tag": "C-201",
        "vibration_mms": 6.8,  # > 4.5 mm/s ISO 10816 limit
        "reason": "Motor drive bearing severe vibration excursion",
    }

    result = evaluate_automation_trigger(
        db=test_db,
        trigger_type="VIBRATION_SPIKE",
        site_id="plant-mumbai-01",
        context_data=context,
        dry_run=False,
    )

    assert result["triggered_count"] >= 1
    action = result["actions"][0]
    assert action["status"] == "EXECUTED_AUTONOMOUSLY"
    assert action["approval_threshold"] == "AUTONOMOUS"

    # Verification in DB
    record = test_db.query(ApprovalRecord).filter(ApprovalRecord.approval_id == action["approval_id"]).first()
    assert record.status == "AUTONOMOUS_EXECUTED"


def test_evaluation_remediation_lifecycle(test_db):
    # Flag low-faithfulness query
    rem = create_remediation(
        test_db,
        score_id="SCORE-12345",
        user_id="reliability-lead-01",
        site_id="plant-mumbai-01",
        reason="Incorrect seal flush plan cited for P-101A",
        incorrect_snippets=["Seal Plan 11 is used"],
        correction_notes="Plant Mumbai Unit 2 uses Plan 53A with pressurized barrier fluid as per OISD-116.",
    )
    assert rem["status"] == "PENDING_REINDEX"
    assert rem["remediation_id"].startswith("REM-")

    # List
    remediations = list_remediations(test_db, site_id="plant-mumbai-01", status="PENDING_REINDEX")
    assert len(remediations) >= 1

    # Update status
    updated = update_remediation_status(
        test_db,
        remediation_id=rem["remediation_id"],
        status="REINDEXED",
        resolved_by="automation-admin",
    )
    assert updated["status"] == "REINDEXED"
    assert updated["resolved_by"] == "automation-admin"


def test_automations_api_endpoints():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        # GET /api/automations/policies
        res = client.get("/api/automations/policies")
        assert res.status_code == 200
        data = res.json()
        assert "policies" in data
        assert len(data["policies"]) >= 3

        # POST /api/automations/evaluate (dry_run)
        eval_res = client.post(
            "/api/automations/evaluate",
            json={
                "trigger_type": "HEALTH_INDEX_CRITICAL",
                "context_data": {"equipment_tag": "P-101B", "health_index": 35},
                "dry_run": True,
            },
        )
        assert eval_res.status_code == 200
        eval_data = eval_res.json()
        assert eval_data["dry_run"] is True
        assert eval_data["triggered_count"] >= 1

        # POST /api/automations/evaluate (live)
        live_res = client.post(
            "/api/automations/evaluate",
            json={
                "trigger_type": "HEALTH_INDEX_CRITICAL",
                "context_data": {"equipment_tag": "P-101B", "health_index": 35},
                "dry_run": False,
            },
        )
        assert live_res.status_code == 200
        live_data = live_res.json()
        approval_id = live_data["actions"][0]["approval_id"]

        # GET /api/automations/queue
        queue_res = client.get("/api/automations/queue?status=PENDING")
        assert queue_res.status_code == 200
        assert any(item["approval_id"] == approval_id for item in queue_res.json()["queue"])

        # POST /api/automations/queue/{id}/action
        action_res = client.post(
            f"/api/automations/queue/{approval_id}/action",
            json={"action": "APPROVED", "notes": "Approved via API"},
        )
        assert action_res.status_code == 200
        assert action_res.json()["approval"]["status"] == "APPROVED"

        # POST /api/automations/remediations
        rem_res = client.post(
            "/api/automations/remediations",
            json={
                "score_id": "SCORE-TEST-API",
                "reason": "Drawing out of date",
                "incorrect_snippets": ["Rev 1 cited"],
                "correction_notes": "Rev 2 drawing approved on 2026-08-15",
            },
        )
        assert rem_res.status_code == 200
        rem_id = rem_res.json()["remediation"]["remediation_id"]

        # GET /api/automations/remediations
        list_rem = client.get("/api/automations/remediations")
        assert list_rem.status_code == 200
        assert any(r["remediation_id"] == rem_id for r in list_rem.json()["remediations"])

        # POST /api/automations/remediations/{id}/status
        status_res = client.post(
            f"/api/automations/remediations/{rem_id}/status",
            json={"status": "RESOLVED"},
        )
        assert status_res.status_code == 200
        assert status_res.json()["remediation"]["status"] == "RESOLVED"

    finally:
        app.dependency_overrides.clear()
