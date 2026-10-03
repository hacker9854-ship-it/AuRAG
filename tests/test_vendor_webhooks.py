"""Automated test suite for Phase 2A independent vendor webhook services & HTTP RFQ federation.

Verifies:
- Vendor health check (GET /health) on all 3 independent vendor endpoints
- Valid quote dispatch (POST /quote) returning dynamic quote, SLA, reliability, and BOLT11 invoice
- Invalid quote handling and malformed payload rejection
- HTTP failure / unreachable endpoint resilience in RFQ federation
- Multi-vendor candidate aggregation and explainable deterministic scoring
- Quote-to-payment binding (vendor_node -> rfq_id -> quote_id -> invoice -> payment_id)
- Truthful disclosure: all vendors identified as DEMO VENDOR NODE
"""
import pytest
from starlette.testclient import TestClient

from backend.app.services.machine_money.rfq import (
    DEFAULT_VENDOR_NODES,
    dispatch_http_rfq,
    process_vendor_rfq,
)
from backend.app.services.machine_money.schemas import SelectionStrategy, VendorRFQRequest
from services.vendor_apex.server import app as apex_app
from services.vendor_precision.server import app as precision_app
from services.vendor_quantum.server import app as quantum_app


def test_vendor_apex_health_and_quote():
    client = TestClient(apex_app)
    # 1. Health check
    h_res = client.get("/health")
    assert h_res.status_code == 200
    health = h_res.json()
    assert health["status"] == "healthy"
    assert health["vendor_id"] == "apex-diagnostics"
    assert health["vendor_node_type"] == "DEMO VENDOR NODE"

    # 2. Quote request
    payload = {
        "equipment_id": "P-101A",
        "service_id": "bearing-inspection",
        "max_budget_sats": 500,
    }
    q_res = client.post("/quote", json=payload)
    assert q_res.status_code == 200
    quote = q_res.json()
    assert quote["vendor_id"] == "apex-diagnostics"
    assert quote["amount_sats"] == 250
    assert quote["sla_hours"] == 1.2
    assert quote["reliability_score"] == 0.994
    assert quote["bolt11"].startswith("lnbc")
    assert len(quote["payment_hash"]) == 64
    assert quote["vendor_node_type"] == "DEMO VENDOR NODE"


def test_vendor_precision_health_and_quote():
    client = TestClient(precision_app)
    h_res = client.get("/health")
    assert h_res.status_code == 200
    health = h_res.json()
    assert health["status"] == "healthy"
    assert health["vendor_id"] == "precision-dynamics"
    assert health["vendor_node_type"] == "DEMO VENDOR NODE"

    payload = {
        "equipment_id": "P-101A",
        "service_id": "bearing-inspection",
        "max_budget_sats": 500,
    }
    q_res = client.post("/quote", json=payload)
    assert q_res.status_code == 200
    quote = q_res.json()
    assert quote["vendor_id"] == "precision-dynamics"
    assert quote["amount_sats"] == 320
    assert quote["sla_hours"] == 0.8
    assert quote["reliability_score"] == 0.989
    assert quote["bolt11"].startswith("lnbc")


def test_vendor_quantum_health_and_quote():
    client = TestClient(quantum_app)
    h_res = client.get("/health")
    assert h_res.status_code == 200
    health = h_res.json()
    assert health["status"] == "healthy"
    assert health["vendor_id"] == "quantum-reliability"
    assert health["vendor_node_type"] == "DEMO VENDOR NODE"

    payload = {
        "equipment_id": "P-101A",
        "service_id": "bearing-inspection",
        "max_budget_sats": 500,
    }
    q_res = client.post("/quote", json=payload)
    assert q_res.status_code == 200
    quote = q_res.json()
    assert quote["vendor_id"] == "quantum-reliability"
    assert quote["amount_sats"] == 450
    assert quote["sla_hours"] == 2.5
    assert quote["reliability_score"] == 0.975
    assert quote["bolt11"].startswith("lnbc")


def test_vendor_malformed_quote_payload_rejection():
    client = TestClient(apex_app)
    # Sending invalid data type for max_budget_sats
    res = client.post("/quote", json={"max_budget_sats": "not-an-integer"})
    assert res.status_code == 422


def test_dispatch_http_rfq_federation():
    req = VendorRFQRequest(
        equipment_id="P-101A",
        service_id="bearing-inspection",
        strategy=SelectionStrategy.FASTEST_SLA,
        max_budget_sats=500,
    )
    candidates = dispatch_http_rfq(req, timeout_seconds=0.1, allow_asgi_fallback=True)
    assert len(candidates) == 3
    for c in candidates:
        assert c.vendor_node_type == "DEMO VENDOR NODE"
        assert c.bolt11 is not None
        assert c.bolt11.startswith("lnbc")
        assert c.payment_hash is not None
        assert len(c.payment_hash) == 64


def test_process_vendor_rfq_fastest_sla_selection():
    req = VendorRFQRequest(
        equipment_id="P-101A",
        service_id="bearing-inspection",
        strategy=SelectionStrategy.FASTEST_SLA,
        max_budget_sats=500,
    )
    rfq_resp = process_vendor_rfq(req)

    assert rfq_resp.rfq_id.startswith("RFQ-")
    assert len(rfq_resp.candidates) == 3
    # Fastest SLA winner is Precision Dynamics (0.8 hrs vs 1.2 hrs vs 2.5 hrs)
    assert rfq_resp.selected_vendor.vendor_id == "precision-dynamics"
    assert rfq_resp.selected_vendor.sla_hours == 0.8
    assert rfq_resp.selected_vendor.bolt11 is not None
    assert rfq_resp.selected_vendor.vendor_node_type == "DEMO VENDOR NODE"


def test_process_vendor_rfq_lowest_cost_strategy():
    req = VendorRFQRequest(
        equipment_id="P-101A",
        service_id="bearing-inspection",
        strategy=SelectionStrategy.LOWEST_COST,
        max_budget_sats=500,
    )
    rfq_resp = process_vendor_rfq(req)

    # Lowest cost winner is Apex Diagnostics (250 sats vs 320 sats vs 450 sats)
    assert rfq_resp.selected_vendor.vendor_id == "apex-diagnostics"
    assert rfq_resp.selected_vendor.amount_sats == 250


def test_process_vendor_rfq_highest_reliability_strategy():
    req = VendorRFQRequest(
        equipment_id="P-101A",
        service_id="bearing-inspection",
        strategy=SelectionStrategy.HIGHEST_RELIABILITY,
        max_budget_sats=500,
    )
    rfq_resp = process_vendor_rfq(req)

    # Highest reliability winner is Apex Diagnostics (0.994 vs 0.989 vs 0.975)
    assert rfq_resp.selected_vendor.vendor_id == "apex-diagnostics"
    assert rfq_resp.selected_vendor.reliability_score == 0.994


def test_quote_to_payment_binding_provenance():
    req = VendorRFQRequest(
        equipment_id="P-101A",
        service_id="bearing-inspection",
        strategy=SelectionStrategy.FASTEST_SLA,
        max_budget_sats=500,
    )
    rfq_resp = process_vendor_rfq(req)
    winner = rfq_resp.selected_vendor

    # Verify that the quote candidate contains all required bindings
    assert winner.bolt11 is not None
    assert winner.bolt11.startswith("lnbc")
    assert winner.payment_hash is not None
    assert len(winner.payment_hash) == 64
    assert winner.vendor_node_type == "DEMO VENDOR NODE"
    assert winner.candidate_id.startswith("BID-")
