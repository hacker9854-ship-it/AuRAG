"""Deterministic Mock Lightning Provider for tests, CI, and wallet-less demonstrations.
Explicitly labeled MOCK / SIMULATION as required by BOSS Battle honesty rules.
"""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from backend.app.services.machine_money.exceptions import ProviderError, InvoiceExpiredError
from backend.app.services.machine_money.providers.base import LightningProvider
from backend.app.services.machine_money.schemas import (
    BOLT11Invoice,
    InvoiceRequest,
    PaymentReceipt,
    PaymentStatus,
    ProviderHealth,
    utcnow,
)


class MockLightningProvider(LightningProvider):
    """Zero-risk, offline simulated Lightning Provider.
    Clearly designated as MOCK / SIMULATION in all metadata, receipts, and invoices.
    """

    def __init__(self, initial_balance_sats: int = 1_000_000):
        self.provider_name = "mock"
        self.network = "regtest"
        self.balance_sats = initial_balance_sats
        self._invoices: Dict[str, BOLT11Invoice] = {}
        self._preimages: Dict[str, str] = {}
        self._payments: Dict[str, PaymentReceipt] = {}

    async def health(self) -> ProviderHealth:
        """Report mock provider status."""
        return ProviderHealth(
            provider_name="mock",
            provider_mode="MOCK",
            settlement_source="SIMULATED",
            is_live=False,
            is_connected=True,
            network=self.network,
            balance_sats=self.balance_sats,
            node_pubkey="02mocknode0000000000000000000000000000000000000000000000000000000001",
            latency_ms=1.2,
            details={
                "simulation": True,
                "label": "MOCK / SIMULATION",
                "honesty_disclosure": "Deterministic simulation provider for local testing and CI",
            },
        )

    async def create_invoice(self, request: InvoiceRequest) -> BOLT11Invoice:
        """Create a mock BOLT11 payment request with realistic hash and expiry."""
        preimage = secrets.token_hex(32)
        payment_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
        invoice_id = f"mock-inv-{payment_hash[:12]}"
        
        # Format a realistic-looking mock BOLT11 string
        mock_bolt11 = (
            f"lnbcrt{request.amount_sats}u1p"
            f"{payment_hash[:32]}"
            f"mocksimulatedinvoice0000000000000000000000000000000000"
        )
        
        now = utcnow()
        expires_at = now + timedelta(seconds=request.expiry_seconds)

        invoice = BOLT11Invoice(
            invoice_id=invoice_id,
            payment_hash=payment_hash,
            payment_request=mock_bolt11,
            amount_sats=request.amount_sats,
            memo=f"[MOCK / SIMULATION] {request.memo}",
            created_at=now,
            expires_at=expires_at,
            status=PaymentStatus.PENDING,
        )

        self._invoices[payment_hash] = invoice
        self._preimages[payment_hash] = preimage
        return invoice

    async def pay_invoice(self, bolt11: str, max_fee_sats: int = 20) -> PaymentReceipt:
        """Simulate paying a BOLT11 invoice and return a verifiable cryptographic receipt."""
        # Find matching invoice by payment request or synthesize deterministic receipt
        matching_hash = None
        matching_invoice = None
        for p_hash, inv in self._invoices.items():
            if inv.payment_request == bolt11:
                matching_hash = p_hash
                matching_invoice = inv
                break

        now = utcnow()
        if matching_invoice:
            if matching_invoice.expires_at < now:
                matching_invoice.status = PaymentStatus.EXPIRED
                raise InvoiceExpiredError("Mock invoice has expired")
            
            amount_sats = matching_invoice.amount_sats
            preimage = self._preimages.get(matching_hash, secrets.token_hex(32))
            payment_hash = matching_hash
            matching_invoice.status = PaymentStatus.MOCK_PAID
        else:
            # External or simulated ad-hoc invoice
            preimage = secrets.token_hex(32)
            payment_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
            amount_sats = 150  # Default test inspection satoshis

        if self.balance_sats < amount_sats:
            raise ProviderError(f"Insufficient mock wallet balance: {self.balance_sats} < {amount_sats}")

        self.balance_sats -= amount_sats

        receipt = PaymentReceipt(
            receipt_id=f"rcpt-mock-{payment_hash[:10]}",
            payment_hash=payment_hash,
            preimage=preimage,
            amount_sats=amount_sats,
            fee_sats=0,
            provider="mock",
            status=PaymentStatus.MOCK_PAID,
            settled_at=now,
        )

        self._payments[payment_hash] = receipt
        return receipt

    async def check_payment(self, payment_hash: str) -> PaymentReceipt:
        """Query settlement status of a mock transaction."""
        if payment_hash in self._payments:
            return self._payments[payment_hash]

        if payment_hash in self._invoices:
            inv = self._invoices[payment_hash]
            return PaymentReceipt(
                receipt_id=f"rcpt-mock-{payment_hash[:10]}",
                payment_hash=payment_hash,
                preimage=self._preimages.get(payment_hash),
                amount_sats=inv.amount_sats,
                fee_sats=0,
                provider="mock",
                status=inv.status,
                settled_at=inv.created_at,
            )

        raise ProviderError(f"Payment with hash {payment_hash} not found in mock store")
