import os
import pytest
from backend.app.services.machine_money.providers.factory import get_payment_provider

@pytest.fixture(autouse=True)
def configure_test_environment(monkeypatch):
    """Ensure test environment defaults to mock provider and consistent regression settings."""
    monkeypatch.setenv("MACHINE_MONEY_ENABLED", "true")
    monkeypatch.setenv("MACHINE_MONEY_PROVIDER", "mock")
    monkeypatch.setenv("MACHINE_MONEY_NETWORK", "regtest")
    monkeypatch.setenv("MACHINE_MONEY_AUTO_PAY_ENABLED", "true")
    monkeypatch.setenv("MACHINE_MONEY_MAX_AUTOPAY_SATS", "500")
    monkeypatch.setenv("DEMO_STANDALONE", "false")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    # Reset cached payment provider to respect test environment
    get_payment_provider(force_refresh=True)
