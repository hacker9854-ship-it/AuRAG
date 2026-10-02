"""
Comprehensive Failure-Path Audit Test Suite for AuRAG Machine Money (Task 9.3).
Audits all 6 required failure scenarios:
1. Provider offline / settlement failure
2. Graph offline / Neo4j failure
3. Bad quote / invalid inputs
4. Duplicate trigger / idempotency enforcement
5. Expired invoice handling
6. Missing evidence / ungrounded telemetry gating
"""

import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import hashlib
from backend.app.services.machine_money.bolt11 import encode_bolt11
from backend.app.db.database import Base
from backend.app.db.models import PaymentRecord, AuditEvent
from backend.app.services.machine_money.exceptions import (
    InvoiceExpiredError,
    MachineMoneyError,
    PolicyViolationError,
    ProviderError,
    SpendingLimitExceededError,
)
from backend.app.services.machine_money.graph import record_payment_in_graph, get_payment_graph_trail
from backend.app.services.machine_money.providers.mock import MockLightningProvider
from backend.app.services.machine_money.schemas import (
    InvoiceRequest,
    PaymentStatus,
    utcnow,
)
from backend.app.services.machine_money.service import MachineMoneyService


@pytest.fixture
def db_session():
    """In-memory SQLite session for isolated failure-path tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# -----------------------------------------------------------------------------
# 1. PROVIDER OFFLINE / SETTLEMENT FAILURE
# -----------------------------------------------------------------------------
def test_failure_path_provider_offline(db_session, monkeypatch):
    """Failure Path 1: Provider offline or fails settlement.
    Must mark payment as FAILED, deduct 0 sats, and persist retry guidance.
    """
    monkeypatch.setenv("MACHINE_MONEY_PROVIDER", "mock")
    monkeypatch.setenv("MACHINE_MONEY_MAX_AUTOPAY_SATS", "500")
    monkeypatch.setenv("MACHINE_MONEY_AUTO_PAY_ENABLED", "true")

    service = MachineMoneyService()
    initial_balance = service.provider.balance_sats

    # Simulate provider failure during pay_invoice
    async def mock_pay_fail(bolt11):
        raise ProviderError("Connection refused by Lightning node peer")

    monkeypatch.setattr(service.provider, "pay_invoice", mock_pay_fail)

    inv_fail = encode_bolt11(network="bcrt", amount_sats=250, payment_hash_hex=hashlib.sha256(b"fail_test").hexdigest(), description="Fail test")
    record = asyncio.run(
        service.execute_payment(
            db=db_session,
            bolt11=inv_fail,
            amount_sats=250,
            work_order_id="WO-FAIL-01",
            event_id="EVT-FAIL-01",
            confidence=0.95,
        )
    )

    # Assert payment marked FAILED
    assert record.status == PaymentStatus.FAILED.value
    assert record.error_code == "PROVIDER_PAY_FAILED"
    assert "Connection refused" in record.error_message
    assert service.provider.balance_sats == initial_balance

    # Assert Audit event logged with retry remediation
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.action_type == "PAYMENT_SETTLEMENT_FAILED"
    ).first()
    assert audit is not None
    assert audit.resource_id == record.payment_id
    assert "retry_guidance" in audit.details_json


# -----------------------------------------------------------------------------
# 2. GRAPH OFFLINE / NEO4J FAILURE
# -----------------------------------------------------------------------------
def test_failure_path_graph_offline_recording():
    """Failure Path 2a: Neo4j connection drops during graph lineage writing.
    Must log warning and return False without crashing the caller.
    """
    mock_session = MagicMock()
    mock_session.run.side_effect = Exception("Neo4j BoltConnectionReset: Connection closed by peer")

    success = record_payment_in_graph(
        session=mock_session,
        payment_id="PAY-GRAPH-FAIL",
        payment_hash="hash123",
        preimage="pre123",
        amount_sats=250,
        provider="mock",
        status="SETTLED",
    )

    # Must return False gracefully without raising unhandled exception
    assert success is False


def test_failure_path_graph_offline_trail_lookup():
    """Failure Path 2b: Neo4j query failure during trail lookup.
    Must return structured fallback dict with found=False and error info.
    """
    mock_session = MagicMock()
    mock_session.run.side_effect = Exception("Neo4j database unavailable")

    trail = get_payment_graph_trail(session=mock_session, payment_id="PAY-GRAPH-LOOKUP-FAIL")
    assert trail["found"] is False
    assert "error" in trail or "explanation" in trail


# -----------------------------------------------------------------------------
# 3. BAD QUOTE / INVALID INPUTS
# -----------------------------------------------------------------------------
def test_failure_path_bad_quote_unknown_service():
    """Failure Path 3: Quote requested for unregistered service ID.
    Must fall back to sensible deterministic defaults without crashing.
    """
    service = MachineMoneyService()
    quote = service.generate_quote(
        equipment_id="P-101A",
        service_id="non-existent-subsea-service-999",
    )
    assert quote.equipment_id == "P-101A"
    assert quote.cost_sats > 0
    assert len(quote.parts_included) > 0
    assert quote.service_description is not None


# -----------------------------------------------------------------------------
# 4. DUPLICATE TRIGGER / IDEMPOTENCY
# -----------------------------------------------------------------------------
def test_failure_path_duplicate_trigger(db_session, monkeypatch):
    """Failure Path 4: Re-triggering with identical idempotency key.
    Must return existing record, preventing duplicate Lightning charges.
    """
    monkeypatch.setenv("MACHINE_MONEY_PROVIDER", "mock")
    monkeypatch.setenv("MACHINE_MONEY_MAX_AUTOPAY_SATS", "500")
    monkeypatch.setenv("MACHINE_MONEY_AUTO_PAY_ENABLED", "true")

    service = MachineMoneyService()
    idemp_key = f"idemp-test-{uuid.uuid4().hex[:8]}"

    inv_idemp = encode_bolt11(network="bcrt", amount_sats=250, payment_hash_hex=hashlib.sha256(b"idemp_test").hexdigest(), description="Idemp test")
    # First execution
    rec1 = asyncio.run(
        service.execute_payment(
            db=db_session,
            bolt11=inv_idemp,
            amount_sats=250,
            idempotency_key=idemp_key,
            confidence=0.95,
        )
    )
    assert rec1.status == PaymentStatus.MOCK_PAID.value

    # Second execution with identical idempotency key
    rec2 = asyncio.run(
        service.execute_payment(
            db=db_session,
            bolt11=inv_idemp,
            amount_sats=250,
            idempotency_key=idemp_key,
            confidence=0.95,
        )
    )

    # Must return exact same payment record
    assert rec2.payment_id == rec1.payment_id
    total_records = db_session.query(PaymentRecord).filter(
        PaymentRecord.idempotency_key == idemp_key
    ).count()
    assert total_records == 1, "Duplicate payment record was created!"


# -----------------------------------------------------------------------------
# 5. EXPIRED INVOICE
# -----------------------------------------------------------------------------
def test_failure_path_expired_invoice(db_session, monkeypatch):
    """Failure Path 5: Attempting to settle an expired BOLT11 invoice.
    Mock provider raises InvoiceExpiredError; service marks payment FAILED.
    """
    monkeypatch.setenv("MACHINE_MONEY_PROVIDER", "mock")
    monkeypatch.setenv("MACHINE_MONEY_MAX_AUTOPAY_SATS", "500")
    monkeypatch.setenv("MACHINE_MONEY_AUTO_PAY_ENABLED", "true")

    provider = MockLightningProvider()
    service = MachineMoneyService()
    service.provider = provider

    async def run_expired():
        # Create an invoice that expires immediately (in the past)
        req = InvoiceRequest(
            amount_sats=250,
            memo="Expired invoice test",
            expiry_seconds=60,
        )
        invoice = await provider.create_invoice(req)
        # Manually force expires_at to be in the past
        invoice.expires_at = utcnow() - timedelta(minutes=10)

        # Attempting to pay directly to provider raises InvoiceExpiredError
        with pytest.raises(InvoiceExpiredError):
            await provider.pay_invoice(invoice.payment_request)

        # Attempting to pay via service marks record FAILED with proper audit
        record = await service.execute_payment(
            db=db_session,
            bolt11=invoice.payment_request,
            amount_sats=250,
            confidence=0.95,
        )
        return record

    record = asyncio.run(run_expired())
    assert record.status == PaymentStatus.FAILED.value
    assert "expired" in record.error_message.lower()


# -----------------------------------------------------------------------------
# 6. MISSING EVIDENCE / UNGROUNDED TELEMETRY
# -----------------------------------------------------------------------------
def test_failure_path_missing_evidence_low_confidence(db_session, monkeypatch):
    """Failure Path 6: Low confidence or ungrounded telemetry excursion.
    Policy gate rejects autonomous settlement; payment is held in PENDING_APPROVAL.
    """
    monkeypatch.setenv("MACHINE_MONEY_PROVIDER", "mock")
    monkeypatch.setenv("MACHINE_MONEY_MAX_AUTOPAY_SATS", "500")
    monkeypatch.setenv("MACHINE_MONEY_AUTO_PAY_ENABLED", "true")

    service = MachineMoneyService()

    # Confidence 0.40 is far below the required 0.70 threshold
    inv_lowconf = encode_bolt11(network="bcrt", amount_sats=250, payment_hash_hex=hashlib.sha256(b"low_conf_test").hexdigest(), description="Low conf test")
    record = asyncio.run(
        service.execute_payment(
            db=db_session,
            bolt11=inv_lowconf,
            amount_sats=250,
            confidence=0.40,  # Un-grounded anomaly
        )
    )

    # Must NOT settle autonomously
    assert record.status == PaymentStatus.PENDING_APPROVAL.value
    assert record.preimage is None
    assert record.approval_id is not None

    # Approval record should reflect PENDING approval
    from backend.app.db.models import ApprovalRecord
    approval = db_session.query(ApprovalRecord).filter(
        ApprovalRecord.approval_id == record.approval_id
    ).first()
    assert approval is not None
    assert approval.status == "PENDING"
    assert "confidence" in approval.payload_json
