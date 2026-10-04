"""End-to-End Test Suite for Machine Money (Section 26: Tests 1 - 17).

Validates complete system integration across:
- Existing industrial baseline & graph ontology
- Telemetry anomaly triggers & GraphRAG evidence
- Service catalog quotes & spending policy governance
- Lightning invoice generation & settlement execution
- Deterministic idempotency & anti-double-spend guards
- Dual-layer persistence (PostgreSQL/SQLite + Neo4j graph)
- Human-in-the-loop approval workflows & failure paths
"""
import os
import uuid
import pytest
import hashlib
from fastapi.testclient import TestClient

from backend.app.core.neo4j import get_session
from backend.app.db.database import get_db, init_db
from backend.app.db.models import PaymentRecord
from backend.app.main import app
from backend.app.services.machine_money.bolt11 import encode_bolt11
from backend.app.services.machine_money.registry import DEMO_SERVICES, generate_idempotency_key
from backend.app.services.machine_money.schemas import PaymentStatus

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure mock provider and baseline policies are active for tests."""
    os.environ["MACHINE_MONEY_ENABLED"] = "true"
    os.environ["MACHINE_MONEY_PROVIDER"] = "mock"
    os.environ["MACHINE_MONEY_NETWORK"] = "regtest"
    os.environ["MACHINE_MONEY_AUTO_PAY_ENABLED"] = "true"
    os.environ["MACHINE_MONEY_MAX_AUTOPAY_SATS"] = "500"
    init_db()


# -----------------------------------------------------------------------------
# Test 1 — Existing Baseline Health & API Regression (Section 26.1)
# -----------------------------------------------------------------------------
def test_e2e_01_baseline_health_regression():
    """Verify core application health and Machine Money subsystem readiness."""
    res_live = client.get("/api/health/live")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"

    res_ready = client.get("/api/health/ready")
    assert res_ready.status_code == 200

    mm_health = client.get("/api/machine-money/health")
    assert mm_health.status_code == 200
    data = mm_health.json()
    assert data["provider_name"] in ("mock", "MockLightningProvider", "lnbits", "LNbitsProvider")
    assert data["is_connected"] is True
    assert data["network"] in ("regtest", "signet")
    assert data["balance_sats"] >= 0


# -----------------------------------------------------------------------------
# Test 2 — Neo4j Knowledge Graph Reachability & Seed Entities (Section 26.2)
# -----------------------------------------------------------------------------
def test_e2e_02_neo4j_graph_entities():
    """Verify Neo4j graph driver or fallback graph provides industrial ontology."""
    session = next(get_session())
    assert session is not None

    # Query equipment entities
    result = session.run("MATCH (e:Equipment) RETURN e")
    records = result.data()
    assert len(records) > 0
    tags = [r.get("tag_id") or r.get("id") for r in records]
    assert "P-101A" in tags


# -----------------------------------------------------------------------------
# Test 3 & 4 — Telemetry Trigger & GraphRAG Evidence Linking (Section 26.6 & 26.7)
# -----------------------------------------------------------------------------
def test_e2e_03_telemetry_trigger_and_graphrag_evidence():
    """Verify high-risk telemetry excursion links to GraphRAG failure signatures and procedures."""
    event_id = f"EVT-VIB-E2E-{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/machine-money/trigger-from-telemetry",
        json={
            "equipment_tag": "P-101A",
            "event_id": event_id,
            "failure_event_id": "FE-001",
            "confidence": 0.94,
            "work_order_id": "WO-2026-P101",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value)
    assert data["amount_sats"] == 250
    assert "FE-001" in data["evidence_package"]["evidence"]
    assert "WO-1002" in data["evidence_package"]["evidence"]
    assert "PROC-001" in data["evidence_package"]["evidence"]
    assert "cross_layer_justification" in data["evidence_package"]


# -----------------------------------------------------------------------------
# Test 5 — Service Quote Generation (Section 26.8)
# -----------------------------------------------------------------------------
def test_e2e_04_service_quote_generation():
    """Verify service quote delivers price in satoshis, provider node, and SLA specs."""
    res = client.post(
        "/api/machine-money/quote",
        json={
            "equipment_id": "P-101A",
            "service_id": "bearing-inspection",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["equipment_id"] == "P-101A"
    assert data["cost_sats"] == 250
    assert "High-Frequency Vibration" in data["service_description"]
    assert len(data["parts_included"]) > 0


# -----------------------------------------------------------------------------
# Test 6 — Policy Below Cap: Autonomous Settlement (Section 26.9)
# -----------------------------------------------------------------------------
def test_e2e_05_policy_below_cap_autonomous():
    """Verify payments below the 500 sat cap execute autonomously without human pause."""
    res = client.post(
        "/api/machine-money/simulate",
        json={
            "site_id": "plant-mumbai-01",
            "equipment_id": "P-101A",
            "service_id": "bearing-inspection",
            "amount_sats": 250,
            "confidence": 0.95,
        },
    )
    assert res.status_code == 200
    data = sim_data = res.json()
    assert sim_data["dry_run"] is True
    assert sim_data["amount_sats"] == 250
    assert sim_data["projected_action"] == "AUTONOMOUS_EXECUTE_LIGHTNING_PAYMENT"
    assert sim_data["policy_evaluation"]["authorized"] is True


# -----------------------------------------------------------------------------
# Test 7 — Policy Above Cap: Human Approval Escalation (Section 26.9)
# -----------------------------------------------------------------------------
def test_e2e_06_policy_above_cap_requires_approval():
    """Verify payments exceeding the 500 sat cap require human-in-the-loop authorization."""
    res = client.post(
        "/api/machine-money/simulate",
        json={
            "site_id": "plant-mumbai-01",
            "equipment_id": "P-101A",
            "service_id": "bearing-inspection",
            "amount_sats": 1200,
            "confidence": 0.95,
        },
    )
    assert res.status_code == 200
    sim_data = res.json()
    assert sim_data["projected_action"] == "ROUTE_TO_HUMAN_APPROVAL_QUEUE"
    assert sim_data["policy_evaluation"]["authorized"] is False


# -----------------------------------------------------------------------------
# Test 8 & 9 — Invoice Creation & Lightning Payment Settlement (Section 26.10 & 26.11)
# -----------------------------------------------------------------------------
def test_e2e_07_invoice_and_payment_settlement():
    """Verify BOLT11 invoice generation and settlement transition to PAID."""
    inv_res = client.post(
        "/api/machine-money/invoice",
        json={
            "amount_sats": 250,
            "memo": "E2E Bearing Inspection",
            "equipment_id": "P-101A",
            "event_id": f"EVT-INV-{uuid.uuid4().hex[:6]}",
        },
    )
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    bolt11 = inv_data["invoice"]
    assert bolt11.startswith("lnbc") or bolt11.startswith("lntbs") or bolt11.startswith("lnsb") or bolt11.startswith("lntb")
    assert inv_data["payment_hash"] is not None

    pay_res = client.post(
        "/api/machine-money/pay",
        json={
            "bolt11": bolt11,
            "amount_sats": 250,
            "work_order_id": "WO-E2E-101",
            "confidence": 0.95,
        },
    )
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    assert pay_data["status"] in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value)
    assert pay_data["preimage"] is not None


# -----------------------------------------------------------------------------
# Test 10 — Deterministic Idempotency & Zero Double-Spend (Section 26.12)
# -----------------------------------------------------------------------------
def test_e2e_08_deterministic_idempotency_guard():
    """Verify re-submitting an identical payment intent prevents duplicate settlement."""
    evt_id = f"EVT-IDEMP-{uuid.uuid4().hex[:6]}"
    payload = {
        "equipment_tag": "P-101A",
        "event_id": evt_id,
        "failure_event_id": "FE-001",
        "confidence": 0.94,
        "work_order_id": "WO-2026-P101",
    }
    # Initial trigger
    res1 = client.post("/api/machine-money/trigger-from-telemetry", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["is_duplicate_prevented"] is False

    # Second trigger with exact same parameters
    res2 = client.post("/api/machine-money/trigger-from-telemetry", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["payment_id"] == data1["payment_id"]
    assert data2["is_duplicate_prevented"] is True


# -----------------------------------------------------------------------------
# Test 11 & 12 — Relational & Neo4j Graph Persistence (Section 26.13 & 26.14)
# -----------------------------------------------------------------------------
def test_e2e_09_relational_and_graph_persistence():
    """Verify payment record is committed to SQL database and Neo4j causal graph."""
    evt_id = f"EVT-GRAPH-{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/machine-money/trigger-from-telemetry",
        json={
            "equipment_tag": "P-101A",
            "event_id": evt_id,
            "failure_event_id": "FE-001",
            "confidence": 0.94,
            "work_order_id": "WO-2026-P101",
        },
    )
    assert res.status_code == 200
    pid = res.json()["payment_id"]

    # 1. SQL Record Verification
    db = next(get_db())
    rec = db.query(PaymentRecord).filter(PaymentRecord.payment_id == pid).first()
    assert rec is not None
    assert rec.amount_sats == 250
    assert rec.status in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value)

    # 2. Graph Trail Verification
    trail_res = client.get(f"/api/machine-money/payments/{pid}/trail")
    assert trail_res.status_code == 200
    trail = trail_res.json()
    assert trail["found"] is True
    assert trail["equipment"]["tag_id"] == "P-101A"
    assert trail["service_provider"] is not None


# -----------------------------------------------------------------------------
# Test 13 & 14 — Audit Record & Human Operator Approval Gate (Section 26.15 & 26.17)
# -----------------------------------------------------------------------------
def test_e2e_10_human_operator_approval_workflow():
    """Verify a transaction held in PENDING_APPROVAL can be signed off by a human engineer."""
    inv_res = client.post(
        "/api/machine-money/invoice",
        json={
            "amount_sats": 1200,  # Exceeds 500 sat cap
            "memo": "Motor Stator Rewind",
            "equipment_id": "P-101A",
        },
    )
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    bolt11 = inv_data["invoice"]

    # Attempt payment without bypass: policy holds it in PENDING_APPROVAL
    pay_res = client.post(
        "/api/machine-money/pay",
        json={
            "bolt11": bolt11,
            "amount_sats": 1200,
            "work_order_id": "WO-APPROVAL-101",
            "bypass_policy": False,
        },
    )
    assert pay_res.status_code == 200
    held_data = pay_res.json()
    assert held_data["status"] == PaymentStatus.PENDING_APPROVAL.value
    held_pid = held_data["payment_id"]

    # Operator performs formal review and sign-off
    appr_res = client.post(
        f"/api/machine-money/payments/{held_pid}/approve",
        json={
            "reviewer_id": "lead-operator-mumbai",
            "review_notes": "Operator sign-off granted to avert critical production stoppage.",
        },
    )
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["status"] in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value)
    assert appr_data["preimage"] is not None


# -----------------------------------------------------------------------------
# Test 15 & 16 — Governed Agent Action Boundary (Section 26.15 & 26.17)
# -----------------------------------------------------------------------------
def test_e2e_11_governed_agent_tool_boundary():
    """Verify LLM agent proposals are strictly bound by backend policy validation."""
    # 1. Compliant proposal executes autonomously
    valid_res = client.post(
        "/api/machine-money/agent-tool",
        json={
            "action": "PAY_FOR_SERVICE",
            "service_id": "bearing-inspection",
            "equipment_tag": "P-101A",
            "reason": "Vibration excursion matches FE-001",
            "evidence": ["FE-001", "WO-1002", "PROC-001"],
            "confidence": 0.94,
            "event_id": f"EVT-AGENT-{uuid.uuid4().hex[:6]}",
        },
    )
    assert valid_res.status_code == 200
    v_data = valid_res.json()
    assert v_data["status"] in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value)
    assert v_data["amount_sats"] == 250

    # 2. Invalid service proposed by agent -> Rejected by backend
    invalid_res = client.post(
        "/api/machine-money/agent-tool",
        json={
            "action": "PAY_FOR_SERVICE",
            "service_id": "unapproved-external-service",
            "equipment_tag": "P-101A",
        },
    )
    assert invalid_res.status_code == 400


# -----------------------------------------------------------------------------
# Test 17 — Failure Paths & Resilience (Section 26.17)
# -----------------------------------------------------------------------------
def test_e2e_12_failure_paths_and_resilience():
    """Verify safe error handling for non-existent payments and invalid quotes."""
    # 1. Non-existent payment lookup returns 404
    missing_res = client.get("/api/machine-money/payments/NON-EXISTENT-PAYMENT-ID")
    assert missing_res.status_code == 404

    # 2. Approving a non-existent payment returns 400
    invalid_appr = client.post(
        "/api/machine-money/payments/NON-EXISTENT-PAYMENT-ID/approve",
        json={"reviewer_id": "test"},
    )
    assert invalid_appr.status_code == 400

    # 3. Invalid tool action returns 400
    invalid_action = client.post(
        "/api/machine-money/agent-tool",
        json={
            "action": "INVALID_UNKNOWN_ACTION",
            "service_id": "bearing-inspection",
            "equipment_tag": "P-101A",
        },
    )
    assert invalid_action.status_code == 400


# -----------------------------------------------------------------------------
# Phase 7 — Task 7.1: Autonomous Happy-Path E2E Lifecycle
# trigger → evidence → rfq → policy → invoice → settlement → audit → graph → economics
# -----------------------------------------------------------------------------
def test_e2e_13_complete_autonomous_lifecycle_e2e():
    """Verify complete 9-stage autonomous lifecycle from vibration trigger to economics impact."""
    import hashlib

    # 1. TRIGGER: Real-time sensor anomaly on high-criticality charge pump P-101A
    event_id = f"EVT-AUTO-E2E-{uuid.uuid4().hex[:8]}"
    trigger_payload = {
        "equipment_tag": "P-101A",
        "event_id": event_id,
        "failure_event_id": "FE-001",
        "confidence": 0.94,
        "work_order_id": "WO-2026-P101",
    }
    trigger_res = client.post("/api/machine-money/trigger-from-telemetry", json=trigger_payload)
    assert trigger_res.status_code == 200
    trigger_data = trigger_res.json()

    # 2. EVIDENCE: Cross-layer failure signature and procedure grounding
    evidence_pkg = trigger_data["evidence_package"]
    assert "FE-001" in evidence_pkg["evidence"]
    assert "PROC-001" in evidence_pkg["evidence"]
    assert "WO-1002" in evidence_pkg["evidence"]
    assert evidence_pkg["confidence"] == 0.94

    # 3. RFQ: Candidate quotation resolved
    service_info = trigger_data["service"]
    assert service_info["id"] == "bearing-inspection"
    assert "node" in service_info["provider"].lower() or "industrial" in service_info["provider"].lower()

    # 4. POLICY: Spending limit verified (250 sats <= 500 sat cap)
    amount_sats = trigger_data["amount_sats"]
    assert amount_sats == 250
    assert amount_sats <= 500  # Within autonomous cap

    # 5. INVOICE: BOLT11 invoice and payment hash generated
    payment_hash = trigger_data["payment_hash"]
    assert payment_hash is not None and len(payment_hash) == 64
    idempotency_key = trigger_data["idempotency_key"]
    assert idempotency_key.startswith("idemp-")

    # 6. SETTLEMENT: Cryptographic payment receipt with preimage
    assert trigger_data["status"] in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value)
    preimage = trigger_data["preimage"]
    assert preimage is not None and len(preimage) == 64
    payment_id = trigger_data["payment_id"]

    # 7. AUDIT: SQL Ledger persistence
    db = next(get_db())
    from backend.app.db.models import AuditEvent
    audit_record = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.action_type == "LIGHTNING_PAYMENT_SETTLED",
            AuditEvent.status == "SUCCESS",
        )
        .order_by(AuditEvent.id.desc())
        .first()
    )
    assert audit_record is not None
    assert payment_id in audit_record.details_json

    # 8. GRAPH: Neo4j operational causal trail
    trail_res = client.get(f"/api/machine-money/payments/{payment_id}/trail")
    assert trail_res.status_code == 200
    trail_data = trail_res.json()
    assert trail_data["found"] is True
    assert trail_data["equipment"]["tag_id"] == "P-101A"

    # 9. ECONOMICS: Industrial impact model validation
    econ_res = client.get("/api/machine-money/analytics/economics")
    assert econ_res.status_code == 200
    econ_data = econ_res.json()
    assert econ_data["equipment_tag"] == "P-101A"
    assert econ_data["downtime_hours_avoided"] == 4.5
    assert econ_data["estimated_downtime_exposure_usd"] == 1170000.0
    assert econ_data["protection_multiple"] > 1000000
    assert econ_data["is_estimated"] is True


# -----------------------------------------------------------------------------
# Phase 7 — Task 7.2: Above-Cap E2E Policy Escalation
# high amount (>500 sats) → policy gate → pending approval → evidence package → operator approve → settle
# -----------------------------------------------------------------------------
def test_e2e_14_policy_escalation_lifecycle_e2e():
    """Verify above-cap payment lifecycle: blocked from autopay, enriched evidence inspectable, approved by human."""
    unique_suffix = uuid.uuid4().hex[:8]
    idemp_key = f"idemp-esc-e2e-{unique_suffix}"

    # 1. Generate Invoice for 1,200 sats (exceeds 500-sat cap)
    inv_res = client.post(
        "/api/machine-money/invoice",
        json={
            "amount_sats": 1200,
            "memo": "Emergency Rotor Dynamic Balancing & Alignment",
            "equipment_id": "P-101A",
            "idempotency_key": idemp_key,
        },
    )
    assert inv_res.status_code == 200
    invoice = inv_res.json()["invoice"]

    # 2. Unilateral bypass rejected if attempted (Task 6.1 boundary check)
    bypass_res = client.post(
        "/api/machine-money/pay",
        json={
            "bolt11": invoice,
            "amount_sats": 1200,
            "bypass_policy": True,
            "idempotency_key": idemp_key,
        },
    )
    assert bypass_res.status_code == 403

    # 3. Standard autonomous attempt routes to PENDING_APPROVAL
    pay_res = client.post(
        "/api/machine-money/pay",
        json={
            "bolt11": invoice,
            "amount_sats": 1200,
            "work_order_id": f"WO-ESC-{unique_suffix}",
            "idempotency_key": idemp_key,
        },
    )
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    assert pay_data["status"] == PaymentStatus.PENDING_APPROVAL.value
    payment_id = pay_data["payment_id"]

    # 4. Human Approval Evidence Package retrieved before sign-off (Task 6.2)
    ev_res = client.get(f"/api/machine-money/payments/{payment_id}/approval-evidence")
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert ev_data["payment_id"] == payment_id
    assert ev_data["amount_sats"] == 1200
    assert ev_data["autonomous_cap_sats"] == 500
    assert ev_data["excess_sats_over_cap"] == 700
    assert "ISO 10816 Zone C" in ev_data["telemetry_excursion"]["standard"]
    assert ev_data["governing_procedure"] == "PROC-001"
    assert ev_data["industrial_economics"]["gross_exposure_usd"] == 1170000.0
    assert len(ev_data["recommended_action"]) > 0
    assert len(ev_data["rollback_guidance"]) > 0

    # 5. Plant reliability engineer executes formal approval sign-off
    appr_res = client.post(
        f"/api/machine-money/payments/{payment_id}/approve",
        json={
            "reviewer_id": "chief-reliability-engineer-mumbai",
            "review_notes": "Emergency rotor alignment verified against ISO 10816 vibration spectrogram.",
        },
    )
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["status"] in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value)
    assert appr_data["preimage"] is not None
    assert len(appr_data["preimage"]) == 64

    # 6. Judge Mode Policy Escalation Scenario E2E
    judge_res = client.post(
        "/api/machine-money/judge/execute",
        json={
            "scenario": "POLICY_ESCALATION",
            "equipment_id": "P-101A",
            "override_cost_sats": 1200,
        },
    )
    assert judge_res.status_code == 200
    judge_data = judge_res.json()
    assert judge_data["status"] == "PENDING_APPROVAL"
    assert judge_data["payment_record"]["status"] == "PENDING_APPROVAL"
    assert judge_data["payment_record"]["amount_sats"] == 1200
    stages = [e["stage"] for e in judge_data["events"]]
    assert "POLICY_EVALUATED" in stages
    assert "SETTLEMENT_CONFIRMED" not in stages


# -----------------------------------------------------------------------------
# Phase 7 — Task 7.3: Provider-Failure E2E Scenario
# simulate liquidity failure → halt at settlement → status FAILED → 0 sats → retry guidance
# -----------------------------------------------------------------------------
def test_e2e_15_provider_failure_lifecycle_e2e():
    """Verify provider failure E2E: halts at settlement, status FAILED, retry guidance in DB audit."""
    import json

    # 1. Execute Judge Mode Provider Failure Scenario
    res = client.post(
        "/api/machine-money/judge/execute",
        json={
            "scenario": "PROVIDER_FAILURE",
            "equipment_id": "P-101A",
            "override_cost_sats": 250,
        },
    )
    assert res.status_code == 200
    data = res.json()

    # 2. Verify Execution Level Failure
    assert data["status"] == "FAILED"
    assert data["scenario"] == "PROVIDER_FAILURE"
    assert "liquidity" in data["summary"].lower() or "failed" in data["summary"].lower()

    # 3. Verify Payment Record: Unsettled, 0 Sats charged
    pay_rec = data["payment_record"]
    assert pay_rec is not None
    assert pay_rec["status"] == "FAILED"
    assert pay_rec["amount_sats"] == 250
    assert "retry_guidance" in pay_rec
    assert "Re-balance payment channel via LSP" in pay_rec["retry_guidance"]

    # 4. Verify Stage Transitions: Halts at SETTLEMENT_CONFIRMED (FAILED), never links graph
    stages = [e["stage"] for e in data["events"]]
    assert "SETTLEMENT_CONFIRMED" in stages
    assert "GRAPH_LINKED" not in stages
    assert "OUTCOME_RESOLVED" not in stages

    fail_event = next(e for e in data["events"] if e["stage"] == "SETTLEMENT_CONFIRMED")
    assert fail_event["status"] == "FAILED"
    assert fail_event["data"]["settled"] is False
    assert "retry_guidance" in fail_event["data"]

    # 5. Verify SQL Audit Record reflects failure and supplies remediation guidance
    db = next(get_db())
    from backend.app.db.models import AuditEvent
    audit = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.action_type == "PAYMENT_SETTLEMENT_FAILED",
            AuditEvent.status == "FAILED",
            AuditEvent.resource_id == pay_rec["payment_id"],
        )
        .first()
    )
    assert audit is not None
    details = json.loads(audit.details_json)
    assert details["error_code"] == "PROVIDER_PAY_FAILED"
    assert "Zero satoshis deducted" in details["retry_guidance"]


# -----------------------------------------------------------------------------
# Phase 7 — Task 7.4: QR Payload Exact BOLT11 Regression
# backend BOLT11 source of truth → zero mutation → exact invoice payload preserved
# -----------------------------------------------------------------------------
def test_e2e_16_qr_payload_exact_bolt11_regression():
    """Verify backend produces exact BOLT11 invoice string preserved identically across all APIs."""
    inv_res = client.post(
        "/api/machine-money/invoice",
        json={
            "amount_sats": 250,
            "memo": "Vibration Sensor Acoustic Analysis P-101A",
            "equipment_id": "P-101A",
        },
    )
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    bolt11 = inv_data["invoice"]
    pid = inv_data["payment_id"]

    # 1. Invoice format adherence: Starts with Lightning prefix, no whitespace, valid charset
    assert bolt11.startswith("lnbc") or bolt11.startswith("lnbcrt") or bolt11.startswith("lntbs") or bolt11.startswith("lnsb") or bolt11.startswith("lntb")
    assert " " not in bolt11
    assert "\n" not in bolt11
    assert "\t" not in bolt11
    assert bolt11.islower() or bolt11.isupper()

    # 2. Payment Record detail API preserves exact BOLT11 string
    pay_res = client.get(f"/api/machine-money/payments/{pid}")
    assert pay_res.status_code == 200
    pay_detail = pay_res.json()
    assert pay_detail["invoice"] == bolt11

    # 3. Proof Package API delivers the identical BOLT11 string for QR renderer consumption
    proof_res = client.get(f"/api/machine-money/payments/{pid}/proof-package")
    assert proof_res.status_code == 200
    proof_pkg = proof_res.json()
    assert proof_pkg["payment"]["bolt11"] == bolt11
    assert proof_pkg["payment"]["amount_sats"] == 250


# -----------------------------------------------------------------------------
# Phase 7 — Task 7.5: Proof-Chain Regression
# payment_hash, preimage, idempotency_key, work_order, predictive_event, policy, graph, sql audit
# -----------------------------------------------------------------------------
def test_e2e_17_complete_payment_proof_chain_regression():
    """Verify complete 8-link payment proof chain across cryptographic, policy, operational, and audit layers."""
    import hashlib

    # Trigger a real autonomous payment
    unique_evt = f"EVT-PROOF-{uuid.uuid4().hex[:8]}"
    res = client.post(
        "/api/machine-money/trigger-from-telemetry",
        json={
            "equipment_tag": "P-101A",
            "event_id": unique_evt,
            "failure_event_id": "FE-001",
            "confidence": 0.94,
            "work_order_id": "WO-2026-P101",
        },
    )
    assert res.status_code == 200
    pay_data = res.json()
    pid = pay_data["payment_id"]

    # Fetch the comprehensive proof package
    proof_res = client.get(f"/api/machine-money/payments/{pid}/proof-package")
    assert proof_res.status_code == 200
    pkg = proof_res.json()

    # 1. payment_hash
    payment_hash = pkg["cryptographic_proof"]["payment_hash"]
    assert payment_hash is not None and len(payment_hash) == 64

    # 2. preimage & SHA-256 verification
    preimage = pkg["cryptographic_proof"]["preimage"]
    assert preimage is not None and len(preimage) == 64
    computed_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
    assert computed_hash.lower() == payment_hash.lower()
    assert pkg["cryptographic_proof"]["is_verified"] is True

    # 3. idempotency_key
    idemp_key = pkg["identity"]["idempotency_key"]
    assert idemp_key.startswith("idemp-")

    # 4. work_order
    work_order = pkg["operational_context"]["work_order_id"]
    assert work_order == "WO-2026-P101"

    # 5. predictive_event
    predictive_event = pkg["operational_context"]["event_id"]
    assert predictive_event == unique_evt

    # 6. policy
    assert pkg["policy"]["policy_id"] == "POL-LIGHTNING-MACHINE-MONEY"
    assert pkg["policy"]["decision"] == "AUTHORIZED"
    assert pkg["policy"]["cap_sats"] == 500

    # 7. graph lineage
    lineage = pkg["graph_links"]["lineage"]
    assert any("Equipment" in node for node in lineage)
    assert any("PredictiveEvent" in node for node in lineage)
    assert any("FailureSignature" in node for node in lineage)
    assert any("WorkOrder" in node for node in lineage)
    assert any("Payment" in node for node in lineage)
    assert any("ServiceProvider" in node for node in lineage)

    # 8. sql audit
    assert pkg["audit"]["audit_ledger_status"] == "SQL_PERSISTED"
    db = next(get_db())
    from backend.app.db.models import AuditEvent
    audit = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.action_type == "LIGHTNING_PAYMENT_SETTLED",
            AuditEvent.status == "SUCCESS",
        )
        .order_by(AuditEvent.id.desc())
        .first()
    )
    assert audit is not None
    assert pid in audit.details_json


# -----------------------------------------------------------------------------
# Phase 1: E2E Invalid & Unregistered BOLT11 Invoice Rejection Guard
# -----------------------------------------------------------------------------
def test_e2e_18_unregistered_and_malformed_invoice_rejection():
    """Verify that posting invalid or unregistered invoices to /api/machine-money/pay fails with 0 sats deducted."""
    # 1. Unregistered valid BOLT11 invoice
    unregistered_hash = hashlib.sha256(b"e2e_unregistered_invoice_test").hexdigest()
    unreg_bolt11 = encode_bolt11(
        network="bcrt",
        amount_sats=250,
        payment_hash_hex=unregistered_hash,
        description="E2E Unregistered invoice test",
    )

    res_unreg = client.post(
        "/api/machine-money/pay",
        json={
            "bolt11": unreg_bolt11,
            "amount_sats": 250,
            "work_order_id": "WO-E2E-UNREG",
            "confidence": 0.95,
        },
    )
    assert res_unreg.status_code == 200
    data_unreg = res_unreg.json()
    assert data_unreg["status"] == "FAILED"
    assert data_unreg["error_code"] == "PROVIDER_PAY_FAILED"
    assert "unregistered" in data_unreg["error_message"].lower()
    assert data_unreg["preimage"] is None

    # 2. Malformed invoice string
    res_malformed = client.post(
        "/api/machine-money/pay",
        json={
            "bolt11": "lnbcrt_not_a_valid_bolt11_string",
            "amount_sats": 250,
            "work_order_id": "WO-E2E-MALFORMED",
            "confidence": 0.95,
        },
    )
    assert res_malformed.status_code == 200
    data_malformed = res_malformed.json()
    assert data_malformed["status"] == "FAILED"
    assert data_malformed["error_code"] == "PROVIDER_PAY_FAILED"
    assert data_malformed["preimage"] is None





