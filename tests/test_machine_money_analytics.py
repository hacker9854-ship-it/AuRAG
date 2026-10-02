"""Unit and integration tests for Machine Money analytics metrics aggregation (Task 5.1)."""
import json
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import Base, PaymentRecord
from backend.app.main import app
from backend.app.services.machine_money.analytics import (
    calculate_machine_money_metrics,
    SETTLED_STATUSES,
)
from backend.app.services.machine_money.schemas import MachineMoneyMetrics


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client():
    return TestClient(app)


def test_analytics_metrics_empty_db(test_db):
    """Verify empty database returns zeroed metrics without calculation or division errors."""
    metrics = calculate_machine_money_metrics(test_db)
    assert isinstance(metrics, MachineMoneyMetrics)
    assert metrics.total_spend_sats == 0
    assert metrics.settled_count == 0
    assert metrics.pending_count == 0
    assert metrics.failed_count == 0
    assert metrics.total_transactions == 0
    assert metrics.autonomous_count == 0
    assert metrics.human_approval_count == 0
    assert metrics.average_settlement_latency_ms == 0.0
    assert metrics.quote_to_payment_conversion_rate == 0.0
    assert metrics.vendor_spend == []


def test_analytics_metrics_settled_and_pending_aggregation(test_db):
    """Task 5.1: Backend calculations for spend, settled, pending, autonomous, and human approvals."""
    now = datetime.now(timezone.utc)

    # 1. Settled autonomous payment
    p1 = PaymentRecord(
        payment_id="PAY-001",
        amount_sats=250,
        fee_sats=1,
        status="SETTLED",
        quote_id="QTE-001",
        created_at=now - timedelta(seconds=2),
        paid_at=now,
        metadata_json=json.dumps({"vendor_name": "Industrial Dynamics Specialist Node"}),
    )

    # 2. Settled autonomous payment
    p2 = PaymentRecord(
        payment_id="PAY-002",
        amount_sats=150,
        fee_sats=1,
        status="PAID",
        quote_id="QTE-002",
        created_at=now - timedelta(seconds=1),
        paid_at=now,
        metadata_json=json.dumps({"vendor_name": "BearingTech Diagnostic Services"}),
    )

    # 3. Settled human-approved payment
    p3 = PaymentRecord(
        payment_id="PAY-003",
        amount_sats=1200,
        fee_sats=2,
        status="SETTLED",
        approval_id="APPV-001",
        quote_id="QTE-003",
        created_at=now - timedelta(seconds=10),
        paid_at=now,
        metadata_json=json.dumps({
            "vendor_name": "Heavy Turbomachinery Overhaul Node",
            "approved_by": "operator-lead",
        }),
    )

    # 4. Pending payment (awaiting operator approval)
    p4 = PaymentRecord(
        payment_id="PAY-004",
        amount_sats=800,
        status="PENDING_APPROVAL",
        quote_id="QTE-004",
        created_at=now,
    )

    # 5. Failed payment
    p5 = PaymentRecord(
        payment_id="PAY-005",
        amount_sats=300,
        status="FAILED",
        created_at=now,
    )

    test_db.add_all([p1, p2, p3, p4, p5])
    test_db.commit()

    metrics = calculate_machine_money_metrics(test_db)

    # Spend metrics
    assert metrics.total_spend_sats == 250 + 150 + 1200  # 1600 sats
    assert metrics.total_spend_msat == 1600 * 1000
    assert metrics.total_fee_sats == 1 + 1 + 2  # 4 sats
    assert metrics.fiat_spend_usd_estimate == round(1600 * 0.00065, 4)

    # Counts
    assert metrics.settled_count == 3
    assert metrics.pending_count == 1
    assert metrics.failed_count == 1
    assert metrics.total_transactions == 5

    # Autonomous vs Human
    assert metrics.autonomous_count == 2
    assert metrics.human_approval_count == 2  # 1 settled approval + 1 pending approval
    assert metrics.autonomous_rate_percentage == round(2 / 3 * 100, 1)  # 66.7%

    # Latency: (2s + 1s + 10s) / 3 = 4.33s = 4333.3ms
    assert 4.0 <= metrics.average_settlement_latency_seconds <= 4.5
    assert 4000 <= metrics.average_settlement_latency_ms <= 4500

    # Vendor spend breakdown
    assert len(metrics.vendor_spend) == 3
    # Heavy Turbomachinery had 1200 sats / 1600 = 75.0%
    heavy = next(v for v in metrics.vendor_spend if "Turbomachinery" in v.vendor_name)
    assert heavy.spend_sats == 1200
    assert heavy.percentage == 75.0
    assert heavy.payment_count == 1

    # Quote-to-payment conversion: 3 converted out of 4 known quotes = 75.0%
    assert metrics.total_quotes_generated == 4
    assert metrics.quotes_converted == 3
    assert metrics.quote_to_payment_conversion_rate == 75.0


def test_analytics_api_endpoint(client):
    """Verify GET /api/machine-money/analytics/metrics returns 200 and schema compliant JSON."""
    response = client.get("/api/machine-money/analytics/metrics")
    assert response.status_code == 200
    data = response.json()

    assert "total_spend_sats" in data
    assert "settled_count" in data
    assert "pending_count" in data
    assert "autonomous_count" in data
    assert "human_approval_count" in data
    assert "average_settlement_latency_ms" in data
    assert "vendor_spend" in data
    assert "quote_to_payment_conversion_rate" in data
    assert "computed_at" in data
