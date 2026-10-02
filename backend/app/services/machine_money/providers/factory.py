"""Provider factory to resolve the active Lightning payment provider based on configuration."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from backend.app.services.machine_money.providers.base import LightningProvider
from backend.app.services.machine_money.providers.mock import MockLightningProvider
from backend.app.services.machine_money.providers.lnbits import LNbitsProvider

_cached_provider: Optional[LightningProvider] = None


def get_payment_provider(force_refresh: bool = False) -> LightningProvider:
    """Returns the singleton instance of the configured LightningProvider.
    Respects MACHINE_MONEY_PROVIDER environment variable ('mock' | 'lnbits').
    """
    global _cached_provider
    if _cached_provider is not None and not force_refresh:
        return _cached_provider

    provider_type = os.environ.get("MACHINE_MONEY_PROVIDER", "mock").strip().lower()

    if provider_type == "lnbits":
        _cached_provider = LNbitsProvider()
    else:
        # Default resilient fallback is the deterministic Mock provider
        _cached_provider = MockLightningProvider()

    return _cached_provider
