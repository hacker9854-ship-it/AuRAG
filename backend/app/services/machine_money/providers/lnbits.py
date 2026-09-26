"""LNbits Lightning Network Provider using asynchronous REST API client.
Complies with LNbits v0.12+ REST endpoints.
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import httpx
from backend.app.services.machine_money.exceptions import ProviderError
from backend.app.services.machine_money.providers.base import LightningProvider
from backend.app.services.machine_money.schemas import (
    BOLT11Invoice,
    InvoiceRequest,
    PaymentReceipt,
    PaymentStatus,
    ProviderHealth,
    utcnow,
)

logger = logging.getLogger(__name__)


class LNbitsProvider(LightningProvider):
    """Production/Regtest LNbits Lightning Provider adapter.
    Enforces separation between read-only invoice keys and outgoing payment admin keys.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        admin_key: Optional[str] = None,
        invoice_key: Optional[str] = None,
        network: str = "regtest",
        timeout_seconds: float = 15.0,
    ):
        self.base_url = (base_url or os.environ.get("LNBITS_BASE_URL", "https://legend.lnbits.com")).rstrip("/")
        self.admin_key = admin_key or os.environ.get("LNBITS_ADMIN_KEY", "")
        self.invoice_key = invoice_key or os.environ.get("LNBITS_INVOICE_KEY", "") or self.admin_key
        self.network = network or os.environ.get("MACHINE_MONEY_NETWORK", "regtest")
        self.timeout = timeout_seconds

    def _headers(self, is_admin: bool = False) -> dict:
        key = self.admin_key if is_admin else self.invoice_key
        if not key:
            raise ProviderError("Missing LNbits API key for requested operation")
        return {
            "X-Api-Key": key,
            "Content-Type": "application/json",
        }

    async def health(self) -> ProviderHealth:
        """Check wallet connection and balance using LNbits wallet API."""
        if not self.admin_key and not self.invoice_key:
            return ProviderHealth(
                provider_name="lnbits",
                is_connected=False,
                network=self.network,
                details={"error": "LNBITS_ADMIN_KEY or LNBITS_INVOICE_KEY is not configured"},
            )

        endpoint = f"{self.base_url}/api/v1/wallet"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(endpoint, headers=self._headers(is_admin=False))
                if res.status_code == 200:
                    data = res.json()
                    balance_msat = data.get("balance", 0)
                    return ProviderHealth(
                        provider_name="lnbits",
                        is_connected=True,
                        network=self.network,
                        balance_sats=balance_msat // 1000,
                        node_pubkey=data.get("id"),
                        details={"wallet_name": data.get("name")},
                    )
                return ProviderHealth(
                    provider_name="lnbits",
                    is_connected=False,
                    network=self.network,
                    details={"http_status": res.status_code, "response": res.text[:200]},
                )
        except Exception as exc:
            logger.warning(f"LNbits health check failed: {exc}")
            return ProviderHealth(
                provider_name="lnbits",
                is_connected=False,
                network=self.network,
                details={"error": str(exc)},
            )

    async def create_invoice(self, request: InvoiceRequest) -> BOLT11Invoice:
        """Create a new Lightning invoice via LNbits API (out=False)."""
        endpoint = f"{self.base_url}/api/v1/payments"
        payload = {
            "out": False,
            "amount": request.amount_sats,
            "memo": request.memo,
            "expiry": request.expiry_seconds,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(endpoint, json=payload, headers=self._headers(is_admin=False))
                if res.status_code not in (200, 201):
                    raise ProviderError(f"LNbits invoice creation failed [{res.status_code}]: {res.text}")

                data = res.json()
                payment_hash = data.get("payment_hash")
                bolt11 = data.get("payment_request")
                now = utcnow()

                return BOLT11Invoice(
                    invoice_id=f"lnbits-inv-{payment_hash[:12]}",
                    payment_hash=payment_hash,
                    payment_request=bolt11,
                    amount_sats=request.amount_sats,
                    memo=request.memo,
                    created_at=now,
                    expires_at=now + timedelta(seconds=request.expiry_seconds),
                    status=PaymentStatus.PENDING,
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"Network error communicating with LNbits: {exc}") from exc

    async def pay_invoice(self, bolt11: str, max_fee_sats: int = 20) -> PaymentReceipt:
        """Pay an external BOLT11 invoice using server Admin key (out=True)."""
        if not self.admin_key:
            raise ProviderError("LNBITS_ADMIN_KEY is required to execute outgoing payments")

        endpoint = f"{self.base_url}/api/v1/payments"
        payload = {
            "out": True,
            "bolt11": bolt11,
            "max_fee": max_fee_sats,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(endpoint, json=payload, headers=self._headers(is_admin=True))
                if res.status_code not in (200, 201):
                    raise ProviderError(f"LNbits payment execution failed [{res.status_code}]: {res.text}")

                data = res.json()
                payment_hash = data.get("payment_hash")
                preimage = data.get("preimage")
                fee_msat = data.get("fee_msat", 0)

                return PaymentReceipt(
                    receipt_id=f"rcpt-lnbits-{payment_hash[:10]}",
                    payment_hash=payment_hash,
                    preimage=preimage,
                    amount_sats=data.get("amount", 0) // 1000 if "amount" in data else 0,
                    fee_sats=fee_msat // 1000 if fee_msat else 0,
                    provider="lnbits",
                    status=PaymentStatus.SETTLED if preimage else PaymentStatus.PENDING,
                    settled_at=utcnow(),
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"Network error sending payment to LNbits: {exc}") from exc

    async def check_payment(self, payment_hash: str) -> PaymentReceipt:
        """Verify whether an invoice has been paid on the Lightning Network."""
        endpoint = f"{self.base_url}/api/v1/payments/{payment_hash}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(endpoint, headers=self._headers(is_admin=False))
                if res.status_code != 200:
                    raise ProviderError(f"Payment check failed [{res.status_code}]: {res.text}")

                data = res.json()
                paid = data.get("paid", False)
                preimage = data.get("preimage")
                amount_msat = data.get("details", {}).get("amount", 0)

                return PaymentReceipt(
                    receipt_id=f"rcpt-lnbits-{payment_hash[:10]}",
                    payment_hash=payment_hash,
                    preimage=preimage,
                    amount_sats=abs(amount_msat) // 1000,
                    fee_sats=data.get("details", {}).get("fee", 0) // 1000,
                    provider="lnbits",
                    status=PaymentStatus.SETTLED if paid else PaymentStatus.PENDING,
                    settled_at=utcnow(),
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"Network error checking payment status: {exc}") from exc
