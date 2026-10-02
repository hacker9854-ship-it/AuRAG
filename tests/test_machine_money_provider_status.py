"""Tests for backend-derived provider status contract (PRD3 Task 1.2)."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_provider_status_contract():
    """Verify that /provider-status returns canonical provider_mode, settlement_source, network, and is_live."""
    res = client.get("/api/v1/machine-money/provider-status")
    assert res.status_code == 200
    data = res.json()

    assert "provider_name" in data
    assert "provider_mode" in data
    assert "settlement_source" in data
    assert "network" in data
    assert "is_live" in data
    assert "is_connected" in data

    # On default mock configuration
    assert data["provider_mode"] in ("MOCK", "LIVE")
    assert data["settlement_source"] in ("SIMULATED", "LIGHTNING_NODE")
    if data["provider_name"] == "mock":
        assert data["provider_mode"] == "MOCK"
        assert data["settlement_source"] == "SIMULATED"
        assert data["is_live"] is False


def test_health_also_includes_provider_mode():
    """Verify that /health also includes the canonical provider_mode and settlement_source."""
    res = client.get("/api/v1/machine-money/health")
    assert res.status_code == 200
    data = res.json()
    assert "provider_mode" in data
    assert "settlement_source" in data
