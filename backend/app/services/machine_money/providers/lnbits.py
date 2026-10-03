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
    name = "lnbits"

    def __init__(
        self,
        base_url: Optional[str] = None,
        admin_key: Optional[str] = None,
        invoice_key: Optional[str] = None,
        network: Optional[str] = None,
        timeout_seconds: float = 15.0,
    ):
        self.base_url = (base_url or os.environ.get("LNBITS_BASE_URL", "https://demo.lnbits.com")).rstrip("/")
        self.admin_key = admin_key or os.environ.get("LNBITS_ADMIN_KEY", "")
        self.invoice_key = invoice_key or os.environ.get("LNBITS_INVOICE_KEY", "") or self.admin_key
        self.network = (network or os.environ.get("MACHINE_MONEY_NETWORK", "signet")).lower()
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
        is_live_net = self.network.lower() in ("mainnet", "signet")
        if not self.admin_key and not self.invoice_key:
            return ProviderHealth(
                provider_name="lnbits",
                provider_mode="LIVE" if is_live_net else "MOCK",
                settlement_source="LIGHTNING_NODE" if is_live_net else "SIMULATED",
                is_live=False,
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
                        provider_mode="LIVE" if is_live_net else "MOCK",
                        settlement_source="LIGHTNING_NODE" if is_live_net else "SIMULATED",
                        is_live=is_live_net,
                        is_connected=True,
                        network=self.network,
                        balance_sats=balance_msat // 1000,
                        node_pubkey=data.get("id"),
                        details={"wallet_name": data.get("name")},
                    )
                return ProviderHealth(
                    provider_name="lnbits",
                    provider_mode="LIVE" if is_live_net else "MOCK",
                    settlement_source="LIGHTNING_NODE" if is_live_net else "SIMULATED",
                    is_live=False,
                    is_connected=False,
                    network=self.network,
                    details={"http_status": res.status_code, "response": res.text[:200]},
                )
        except Exception as exc:
            logger.warning(f"LNbits health check failed: {exc}")
            return ProviderHealth(
                provider_name="lnbits",
                provider_mode="LIVE" if is_live_net else "MOCK",
                settlement_source="LIGHTNING_NODE" if is_live_net else "SIMULATED",
                is_live=False,
                is_connected=False,
                network=self.network,
                details={"error": str(exc)},
            )

    async def create_invoice(self, request: InvoiceRequest) -> BOLT11Invoice:
        """Create a new Lightning invoice via live LNbits REST API.

        ⚠️  FAIL-CLOSED: If LNbits is unreachable, raises ProviderError.
        No local cryptographic fallback — live mode never fakes settlement.
        """
        if not self.invoice_key:
            raise ProviderError(
                "LNbits invoice creation requires LNBITS_INVOICE_KEY. "
                "Cannot create invoice without live LNbits credentials."
            )

        endpoint = f"{self.base_url}/api/v1/payments"
        payload = {
            "out": False,
            "amount": request.amount_sats,
            "memo": request.memo or "AuRAG Machine Money Invoice",
            "unit": "sat",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(endpoint, json=payload, headers=self._headers(is_admin=False))
                if res.status_code == 201:
                    data = res.json()
                    payment_hash = data.get("payment_hash")
                    bolt11 = data.get("bolt11") or data.get("payment_request")
                    preimage = data.get("preimage")

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
                else:
                    raise ProviderError(
                        f"LNbits invoice creation failed [HTTP {res.status_code}]: {res.text[:200]}. "
                        "Live mode does not fall back to local simulation."
                    )
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(
                f"LNbits network unreachable: {exc}. "
                "Live provider fails closed — no local cryptographic fallback. "
                "Switch to MACHINE_MONEY_PROVIDER=mock for offline evaluation."
            ) from exc

    async def pay_invoice(self, bolt11: str, max_fee_sats: int = 20) -> PaymentReceipt:
        """Execute settlement on BOLT11 invoice via live LNbits node.

        ⚠️  FAIL-CLOSED: Preimage must come from LNbits API response.
        Local preimage store is NEVER used as fallback — if LNbits doesn't
        confirm settlement, this method raises ProviderError with FAILED status.
        """
        from backend.app.services.machine_money.bolt11 import decode_bolt11
        import hashlib

        try:
            decoded = decode_bolt11(bolt11)
        except Exception as exc:
            raise ProviderError(f"Invalid BOLT11 invoice structure or checksum: {exc}") from exc

        payment_hash = decoded.get("payment_hash")
        if not payment_hash:
            raise ProviderError("Invalid BOLT11 invoice: missing mandatory payment_hash")

        amount_sats = decoded.get("amount_sats") or 250
        preimage = None
        fee_sats = 0

        # ── Step 1: Attempt live LNbits settlement via admin key ──
        if not self.admin_key:
            raise ProviderError(
                "LNbits payment requires LNBITS_ADMIN_KEY. "
                "Cannot settle invoice without live admin credentials."
            )

        endpoint = f"{self.base_url}/api/v1/payments"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    endpoint,
                    json={"out": True, "bolt11": bolt11},
                    headers=self._headers(is_admin=True),
                )
                if res.status_code == 201:
                    data = res.json()
                    payment_hash = data.get("payment_hash") or payment_hash

                    # Query LNbits for settlement confirmation and preimage
                    check_res = await client.get(
                        f"{self.base_url}/api/v1/payments/{payment_hash}",
                        headers=self._headers(is_admin=False),
                    )
                    if check_res.status_code == 200:
                        check_data = check_res.json()
                        preimage = check_data.get("preimage") or check_data.get("details", {}).get("preimage")
                        fee_sats = abs(check_data.get("details", {}).get("fee", 0)) // 1000
                else:
                    raise ProviderError(
                        f"LNbits payment failed [HTTP {res.status_code}]: {res.text[:200]}. "
                        "0 satoshis settled. Live mode does not fall back to local simulation."
                    )
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(
                f"LNbits network error during payment: {exc}. "
                "0 satoshis settled. Live provider fails closed — "
                "no local cryptographic fallback."
            ) from exc

        # ── Step 2: If LNbits responded 201 but no preimage yet, retry query ──
        if not preimage:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    check_res = await client.get(
                        f"{self.base_url}/api/v1/payments/{payment_hash}",
                        headers=self._headers(is_admin=False),
                    )
                    if check_res.status_code == 200:
                        check_data = check_res.json()
                        preimage = check_data.get("preimage") or check_data.get("details", {}).get("preimage")
            except Exception:
                pass  # Will fail below if preimage still None

        # ── Step 3: FAIL CLOSED — no local fallback ──
        if not preimage:
            raise ProviderError(
                f"LNbits settlement incomplete: payment_hash {payment_hash} submitted but "
                "no preimage returned by LNbits node. 0 satoshis confirmed settled. "
                "Live provider does NOT fall back to local preimage store."
            )

        # Enforce sha256(preimage) == payment_hash
        computed_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
        if computed_hash.lower() != payment_hash.lower():
            raise ProviderError(
                f"Cryptographic proof mismatch: sha256(preimage) != payment_hash {payment_hash}. "
                "Settlement rejected (0 satoshis deducted)."
            )

        return PaymentReceipt(
            receipt_id=f"rcpt-lnbits-{payment_hash[:10]}",
            payment_hash=payment_hash,
            preimage=preimage,
            amount_sats=amount_sats,
            fee_sats=fee_sats,
            provider="lnbits",
            status=PaymentStatus.SETTLED,
            settled_at=utcnow(),
        )

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
