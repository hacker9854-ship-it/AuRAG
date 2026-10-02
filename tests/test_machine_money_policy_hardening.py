import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import hashlib
from backend.app.db.models import Base, PaymentRecord
from backend.app.main import app
from backend.app.services.machine_money.bolt11 import encode_bolt11
from backend.app.services.machine_money.schemas import PaymentStatus
from backend.app.services.machine_money.service import MachineMoneyService

_TEST_HASH = hashlib.sha256(b"turbomachinery_overhaul_1200").hexdigest()
VALID_1200_INVOICE = encode_bolt11(
    network="bcrt",
    amount_sats=1200,
    payment_hash_hex=_TEST_HASH,
    description="Emergency turbomachinery overhaul",
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def mm_service():
    return MachineMoneyService()


def test_client_cannot_bypass_spending_cap_via_api(client):
    """Task 6.1: A client request to /pay with bypass_policy=True and amount > 500 sats must be rejected with 403."""
    response = client.post(
        "/api/machine-money/pay",
        json={
            "bolt11": VALID_1200_INVOICE,
            "amount_sats": 1200,  # Exceeds 500 sat cap
            "bypass_policy": True,
            "vendor_name": "Heavy Turbomachinery Overhaul Node",
        },
    )
    assert response.status_code == 403
    detail = response.json().get("detail", "")
    assert "Policy violation" in detail
    assert "cannot bypass autonomous spending cap" in detail


def test_service_execute_payment_enforces_pending_approval_over_cap(test_db, mm_service):
    """Task 6.1: Backend service unconditionally gates amounts exceeding max_autopay into PENDING_APPROVAL."""
    record = asyncio.run(
        mm_service.execute_payment(
            db=test_db,
            bolt11=VALID_1200_INVOICE,
            amount_sats=1200,
            bypass_policy=True,  # Even if caller passes bypass_policy=True
            vendor_name="Heavy Turbomachinery Overhaul Node",
        )
    )

    # Must NOT be settled autonomously
    assert record.status == PaymentStatus.PENDING_APPROVAL.value
    assert record.approval_id is not None
    assert record.paid_at is None
    assert record.preimage is None


def test_disallowed_payment_only_settles_via_operator_approval(test_db, mm_service):
    """Task 6.1: A payment held in PENDING_APPROVAL can only be settled via explicit human operator sign-off."""
    # 1. Create payment exceeding cap
    record = asyncio.run(
        mm_service.execute_payment(
            db=test_db,
            bolt11=VALID_1200_INVOICE,
            amount_sats=1200,
            vendor_name="Heavy Turbomachinery Overhaul Node",
        )
    )
    assert record.status == PaymentStatus.PENDING_APPROVAL.value

    # 2. Operator signs off
    approved = asyncio.run(
        mm_service.approve_payment(
            db=test_db,
            payment_id=record.payment_id,
            reviewer_id="lead-operator-mumbai",
            review_notes="Authorized emergency overhaul after reviewing spectrogram.",
        )
    )

    # 3. Now successfully settled
    assert approved.status in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value)
    assert approved.preimage is not None
    assert approved.paid_at is not None

