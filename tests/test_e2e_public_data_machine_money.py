"""End-to-end integration test suite for Phase 2A: Public Industrial Data + Machine Money Pipeline.

Validates the complete execution flow:
PUBLIC DATASET REPLAY
    ↓
TELEMETRY EVENT
    ↓
ANOMALY DETECTION
    ↓
GRAPHRAG GROUNDED EVIDENCE
    ↓
HTTP VENDOR RFQ FEDERATION
    ↓
POLICY GATE
    ↓
LIGHTNING INVOICE
    ↓
PAYMENT SETTLEMENT
    ↓
CRYPTOGRAPHIC PROOF PACKAGE

Verifies that provenance (PUBLIC_DATASET, NASA-IMS-T2-REC-042, REPLAY-ASSET-01)
survives all the way from initial sensor replay to the final tamper-evident proof package.
"""
import hashlib
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import Base
from backend.app.services.machine_money.grounding import get_grounded_evidence_package
from backend.app.services.machine_money.rfq import process_vendor_rfq
from backend.app.services.machine_money.schemas import SelectionStrategy, VendorRFQRequest
from backend.app.services.machine_money.service import MachineMoneyService
from telemetry.adapters.base import DataSourceType
from telemetry.adapters.public_dataset import PublicDatasetReplayAdapter


@pytest.fixture
def db_session():
    """In-memory SQLite test session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_e2e_public_dataset_reading_to_anomaly():
    """Step 1 & 2: Public dataset replay generates normalized event and triggers anomaly."""
    adapter = PublicDatasetReplayAdapter(equipment_id="REPLAY-ASSET-01")
    event = adapter.read_event("NASA-IMS-T2-REC-042")

    assert event["equipment_id"] == "REPLAY-ASSET-01"
    assert event["data_source_type"] == DataSourceType.PUBLIC_DATASET
    assert event["replay_mode"] is True
    assert event["vibration_mm_s"] == 5.42
    assert event["is_anomaly"] is True
    assert event["threshold_exceeded"] is True
    assert "NASA IMS" in event["provenance"]["dataset_name"]
    assert event["provenance"]["dataset_record_id"] == "NASA-IMS-T2-REC-042"


def test_e2e_public_dataset_grounding_provenance():
    """Step 3: Grounded evidence matches failure signature with public dataset provenance."""
    evidence = get_grounded_evidence_package(
        session=None,
        equipment_tag="REPLAY-ASSET-01",
        vibration_reading=5.42,
        vibration_threshold=4.5,
        event_id="EVT-PUB-TEST-001",
        data_source_type="PUBLIC_DATASET",
        dataset_name="NASA IMS Bearing Run-to-Failure (Test 2)",
        dataset_record_id="NASA-IMS-T2-REC-042",
    )

    assert evidence["retrieval_method"] == "PUBLIC_DATASET_REPLAY"
    assert evidence["data_source_type"] == "PUBLIC_DATASET"
    assert evidence["dataset_name"] == "NASA IMS Bearing Run-to-Failure (Test 2)"
    assert evidence["dataset_record_id"] == "NASA-IMS-T2-REC-042"
    assert evidence["asset_mapping"] == "REPLAY-ASSET-01"
    assert evidence["vibration_mm_s"] == 5.42
    assert evidence["governing_procedure"] == "PROC-001"
    assert len(evidence["evidence_refs"]) >= 3


def test_e2e_http_rfq_federation_for_replay_asset():
    """Step 4: Real HTTP RFQ dispatch gathers quotes from demo vendor nodes."""
    rfq_req = VendorRFQRequest(
        equipment_id="REPLAY-ASSET-01",
        service_id="bearing-inspection",
        strategy=SelectionStrategy.FASTEST_SLA,
        max_budget_sats=500,
    )
    rfq_res = process_vendor_rfq(rfq_req)

    assert len(rfq_res.candidates) == 3
    assert rfq_res.selected_vendor is not None
    assert rfq_res.selected_vendor.vendor_node_type == "DEMO VENDOR NODE"
    assert rfq_res.selected_vendor.bolt11 is not None
    assert rfq_res.selected_vendor.payment_hash is not None


@pytest.mark.anyio
async def test_e2e_full_chain_public_replay_to_proof_package(db_session):
    """Complete end-to-end test:
    Public Dataset Replay -> Anomaly -> Evidence -> RFQ -> Policy -> Invoice -> Payment -> Proof Package
    """
    service = MachineMoneyService()

    # Execute Judge Mode public dataset replay scenario
    execution = await service.execute_judge_scenario(
        db=db_session,
        scenario="PUBLIC_DATASET_REPLAY",
        equipment_id="REPLAY-ASSET-01",
        override_cost_sats=250,
        auto_approve=True,
    )

    # 1. Execution status check
    assert execution.status == "SUCCESS"
    assert execution.scenario == "PUBLIC_DATASET_REPLAY"
    assert execution.total_elapsed_ms > 0

    # 2. Stage 1: ANOMALY_DETECTED verification
    anomaly_evt = next(e for e in execution.events if e.stage == "ANOMALY_DETECTED")
    assert anomaly_evt.data["data_source_type"] == "PUBLIC_DATASET"
    assert anomaly_evt.data["equipment_id"] == "REPLAY-ASSET-01"
    assert anomaly_evt.data["dataset_record_id"] == "NASA-IMS-T2-REC-042"
    assert anomaly_evt.data["vibration_mms"] == 5.42

    # 3. Stage 2: EVIDENCE_MATCHED verification
    evidence_evt = next(e for e in execution.events if e.stage == "EVIDENCE_MATCHED")
    assert evidence_evt.data["retrieval_method"] == "PUBLIC_DATASET_REPLAY"
    assert evidence_evt.data["dataset_record_id"] == "NASA-IMS-T2-REC-042"
    assert evidence_evt.data["asset_mapping"] == "REPLAY-ASSET-01"

    # 4. Stage 3: POLICY_EVALUATED verification
    policy_evt = next(e for e in execution.events if e.stage == "POLICY_EVALUATED")
    assert policy_evt.status == "SUCCESS"
    assert policy_evt.data["authorized"] is True

    # 5. Stage 4: INVOICE_GENERATED verification
    invoice_evt = next(e for e in execution.events if e.stage == "INVOICE_GENERATED")
    assert invoice_evt.data["bolt11"].startswith("lnbc") or invoice_evt.data["bolt11"].startswith("lntbs") or invoice_evt.data["bolt11"].startswith("lnsb") or invoice_evt.data["bolt11"].startswith("lntb")

    # 6. Stage 5: SETTLEMENT_CONFIRMED verification
    settle_evt = next(e for e in execution.events if e.stage == "SETTLEMENT_CONFIRMED")
    assert settle_evt.status == "SUCCESS"
    preimage = settle_evt.data["preimage"]
    payment_hash = settle_evt.data["payment_hash"]
    computed_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
    assert computed_hash.lower() == payment_hash.lower(), "Cryptographic invariant sha256(preimage) = payment_hash"

    # 7. Proof Package verification (provenance survives to non-secret proof)
    payment_id = execution.payment_record["payment_id"]
    proof_pkg = await service.get_proof_package(db=db_session, payment_id=payment_id)

    assert proof_pkg["identity"]["payment_id"] == payment_id
    assert proof_pkg["cryptographic_proof"]["is_verified"] is True
    assert proof_pkg["cryptographic_proof"]["payment_hash"] == payment_hash
    assert proof_pkg["cryptographic_proof"]["preimage"] == preimage

    # Verify Provenance in operational context
    op_ctx = proof_pkg["operational_context"]
    assert op_ctx["equipment_id"] == "REPLAY-ASSET-01"
    assert op_ctx["data_source_type"] == "PUBLIC_DATASET"
    assert op_ctx["dataset_record_id"] == "NASA-IMS-T2-REC-042"
    assert op_ctx["replay_mode"] is True
    assert "NASA IMS" in op_ctx["dataset_name"]
