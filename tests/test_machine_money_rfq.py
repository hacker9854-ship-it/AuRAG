"""Unit tests for Multi-Vendor Request-For-Quote (RFQ) and Explainable Selection Engine (Phase 4)."""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.machine_money.rfq import (
    get_candidate_quotes_for_service,
    process_vendor_rfq,
)
from backend.app.services.machine_money.schemas import (
    SelectionStrategy,
    VendorRFQRequest,
    VendorRFQResponse,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_rfq_bids_generation_and_synthetic_integrity():
    """Verify candidate quotes generation, synthetic labeling, and future validity window."""
    candidates = get_candidate_quotes_for_service("bearing-inspection", equipment_id="P-101A")
    assert len(candidates) >= 3

    now = datetime.now(timezone.utc)
    for c in candidates:
        assert c.is_synthetic is True
        assert c.amount_sats > 0
        assert c.sla_hours > 0
        assert 0.0 <= c.reliability_score <= 1.0
        assert len(c.vendor_name) > 0
        assert len(c.node_pubkey) == 66  # Compressed secp256k1 pubkey hex length
        assert c.valid_until > now


def test_rfq_selection_fastest_sla_under_cap():
    """FR-04: Fastest SLA selects candidate with minimal dispatch hours under the policy cap."""
    req = VendorRFQRequest(
        equipment_id="P-101A",
        service_id="bearing-inspection",
        strategy=SelectionStrategy.FASTEST_SLA,
        max_budget_sats=500,  # 500 sat autonomous cap
    )
    res = process_vendor_rfq(req)

    assert isinstance(res, VendorRFQResponse)
    assert res.is_synthetic is True
    assert res.policy_cap_sats == 500
    assert len(res.candidates) >= 4

    # Apex Robotics has 1.0h SLA at 320 sats (under 500 cap).
    # Heavy Turbomachinery has 0.5h SLA but costs 1200 sats (exceeds cap).
    # Therefore, Apex Robotics must win!
    assert res.selected_vendor.vendor_id == "apex-industrial-robotics"
    assert res.selected_vendor.sla_hours == 1.0
    assert res.selected_vendor.amount_sats == 320
    assert res.selected_vendor.within_policy_cap is True

    # Rationale must explain the decision
    assert "Fastest dispatch SLA" in res.selection_rationale
    assert "320 sats <= 500 sats cap" in res.selection_rationale


def test_rfq_selection_lowest_cost():
    """FR-04: Lowest cost selects the most economical vendor preserving maintenance funds."""
    req = VendorRFQRequest(
        equipment_id="P-101A",
        service_id="bearing-inspection",
        strategy=SelectionStrategy.LOWEST_COST,
        max_budget_sats=500,
    )
    res = process_vendor_rfq(req)

    # EcoRotary offers 180 sats
    assert res.selected_vendor.vendor_id == "eco-rotary-nodes"
    assert res.selected_vendor.amount_sats == 180
    assert "Lowest satoshi expenditure" in res.selection_rationale


def test_rfq_selection_highest_reliability():
    """FR-04: Highest reliability selects peak historical score under the budget cap."""
    req = VendorRFQRequest(
        equipment_id="P-101A",
        service_id="bearing-inspection",
        strategy=SelectionStrategy.HIGHEST_RELIABILITY,
        max_budget_sats=500,
    )
    res = process_vendor_rfq(req)

    # Apex has 0.99 (99%) reliability under 500 cap
    assert res.selected_vendor.vendor_id == "apex-industrial-robotics"
    assert res.selected_vendor.reliability_score == 0.99
    assert "Peak historical reliability rating" in res.selection_rationale


def test_rfq_selection_balanced():
    """FR-04: Balanced multi-objective composite score optimizes cost, SLA, and reliability."""
    req = VendorRFQRequest(
        equipment_id="P-101A",
        service_id="bearing-inspection",
        strategy=SelectionStrategy.BALANCED,
        max_budget_sats=500,
    )
    res = process_vendor_rfq(req)

    assert res.selected_vendor is not None
    assert res.selected_vendor.within_policy_cap is True
    assert "Optimal multi-objective score" in res.selection_rationale


def test_rfq_budget_cap_escalation():
    """FR-05: When all candidate bids exceed budget cap, escalation warning is flagged."""
    req = VendorRFQRequest(
        equipment_id="P-101A",
        service_id="bearing-inspection",
        strategy=SelectionStrategy.FASTEST_SLA,
        max_budget_sats=100,  # All bearing inspection bids > 100 sats
    )
    res = process_vendor_rfq(req)

    assert res.selected_vendor is not None
    assert res.selected_vendor.within_policy_cap is False
    assert "Warning: All available vendor bids exceed current spending cap" in res.selection_rationale


def test_rfq_api_endpoints(client):
    """Verify POST /api/machine-money/rfq and GET /api/machine-money/rfq/{service_id}."""
    # 1. POST request
    post_resp = client.post(
        "/api/machine-money/rfq",
        json={
            "equipment_id": "P-101A",
            "service_id": "bearing-inspection",
            "strategy": "FASTEST_SLA",
            "max_budget_sats": 500,
        },
    )
    assert post_resp.status_code == 200
    data = post_resp.json()
    assert "rfq_id" in data
    assert data["service_id"] == "bearing-inspection"
    assert len(data["candidates"]) >= 4
    assert data["selected_vendor"]["vendor_id"] == "apex-industrial-robotics"

    # 2. GET request with query params
    get_resp = client.get("/api/machine-money/rfq/bearing-inspection?strategy=LOWEST_COST&max_budget_sats=500")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["selected_vendor"]["vendor_id"] == "eco-rotary-nodes"
    assert get_data["selected_vendor"]["amount_sats"] == 180
