"""FastAPI router for Machine Money endpoints (payment intents, invoices, and proofs)."""
import os
from fastapi import APIRouter, HTTPException
from backend.app.services.machine_money.schemas import ProviderHealth

router = APIRouter(prefix="/machine-money", tags=["machine-money"])


@router.get("/health", response_model=ProviderHealth)
async def machine_money_health():
    """Verify Machine Money subsystem status and configured payment provider."""
    enabled = os.environ.get("MACHINE_MONEY_ENABLED", "true").lower() == "true"
    provider_name = os.environ.get("MACHINE_MONEY_PROVIDER", "mock")
    network = os.environ.get("MACHINE_MONEY_NETWORK", "regtest")

    return ProviderHealth(
        provider_name=provider_name,
        is_connected=enabled,
        network=network,
        balance_sats=100000 if provider_name == "mock" else None,
        details={
            "enabled": enabled,
            "auto_pay_enabled": os.environ.get("MACHINE_MONEY_AUTO_PAY_ENABLED", "false").lower() == "true",
            "max_autopay_sats": int(os.environ.get("MACHINE_MONEY_MAX_AUTOPAY_SATS", "500")),
        }
    )
