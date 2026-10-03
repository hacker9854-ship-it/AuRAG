"""NIP-47-inspired NWC Provider (experimental simulation) for AuRAG.

Implements the abstract LightningProvider interface using NIP-47-compatible
event structures in local loopback mode. This is a stretch-goal simulation;
primary production settlement uses LNbits BOLT11.
"""

import hashlib
import time
from typing import Optional

from backend.app.services.machine_money.bolt11 import decode_bolt11, encode_bolt11
from backend.app.services.machine_money.nwc import NWCClient
from backend.app.services.machine_money.providers.base import LightningProvider
from backend.app.services.machine_money.schemas import (
    BOLT11Invoice,
    InvoiceRequest,
    PaymentReceipt,
    PaymentStatus,
    ProviderHealth,
)


class NWCProvider(LightningProvider):
    """NIP-47-inspired experimental simulation provider (local loopback, no live relay)."""
    name = "nwc"

    def __init__(self, uri_or_config: Optional[str] = None):
        self.name = "nwc"
        self.client = NWCClient(uri_or_config)

    async def health(self) -> ProviderHealth:
        """Check Nostr relay connectivity and NWC wallet info."""
        info = self.client.get_info()
        balance_info = self.client.get_balance()
        return ProviderHealth(
            provider_name="nwc",
            is_connected=True,
            network="nostr-relay / regtest",
            balance_sats=balance_info.get("balance_sats", 210000),
            provider_mode="NWC / NOSTR WALLET CONNECT",
            settlement_source="NOSTR_RELAY",
            is_live=False,
            details={
                "relay": info["relay"],
                "wallet_pubkey": info["wallet_pubkey"][:16] + "...",
                "client_pubkey": info["client_pubkey"][:16] + "...",
                "lud16": info["lud16"],
                "supported_methods": info["supported_methods"],
            },
        )

    async def create_invoice(self, request: InvoiceRequest) -> BOLT11Invoice:
        """Create a verifiable BOLT11 invoice for the requested payment amount."""
        payment_hash = hashlib.sha256(f"NWC-INV-{request.amount_sats}-{time.time()}".encode()).hexdigest()
        bolt11 = encode_bolt11(amount_sats=request.amount_sats, description=request.memo, payment_hash_hex=payment_hash)
        return BOLT11Invoice(
            bolt11=bolt11,
            payment_request=bolt11,
            payment_hash=payment_hash,
            amount_sats=request.amount_sats,
            expiry_seconds=3600,
            invoice_id=f"nwc-inv-{payment_hash[:12]}",
            memo=request.memo,
        )

    async def pay_invoice(self, bolt11: str, max_fee_sats: int = 20) -> PaymentReceipt:
        """Pay a BOLT11 invoice over NIP-47 remote wallet connection."""
        receipt_data = await self.client.pay_invoice(bolt11, max_fee_sats=max_fee_sats)
        return PaymentReceipt(
            payment_hash=receipt_data["payment_hash"],
            preimage=receipt_data["preimage"],
            amount_sats=receipt_data["amount_sats"],
            fee_sats=receipt_data["fee_sats"],
            status=PaymentStatus.SETTLED,
            provider="nwc",
            settled_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            bolt11=bolt11,
        )

    async def check_payment(self, payment_hash: str) -> PaymentReceipt:
        """Query settlement status of an invoice."""
        preimage = hashlib.sha256(bytes.fromhex(payment_hash) + b":NWC:SETTLEMENT").hexdigest()
        return PaymentReceipt(
            payment_hash=payment_hash,
            preimage=preimage,
            amount_sats=250,
            fee_sats=1,
            status=PaymentStatus.SETTLED,
            provider="nwc",
            settled_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
