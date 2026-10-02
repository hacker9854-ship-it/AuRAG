"""Unit and integration tests for pure Python BOLT11 encoder and decoder.
Verifies compliance with Lightning Network BOLT #11 and BIP 173 Bech32 standards.
"""

import pytest
import asyncio
import hashlib
from backend.app.services.machine_money.bolt11 import (
    MOCK_NODE_PUBKEY,
    decode_bolt11,
    encode_bolt11,
    is_valid_bolt11,
)
from backend.app.services.machine_money.providers.mock import MockLightningProvider
from backend.app.services.machine_money.schemas import InvoiceRequest


def test_bolt11_encode_decode_roundtrip():
    """Verify that an encoded invoice decodes to exact payment parameters with verified signature."""
    payment_hash = "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b"
    memo = "[MOCK / SIMULATION] Micro-payment for P-101A lubrication"
    amount = 250
    timestamp = 1700000000
    expiry = 3600

    invoice = encode_bolt11(
        network="bcrt",
        amount_sats=amount,
        payment_hash_hex=payment_hash,
        description=memo,
        timestamp=timestamp,
        expiry_seconds=expiry,
    )

    assert invoice.startswith("lnbcrt2500n1")
    assert is_valid_bolt11(invoice) is True

    dec = decode_bolt11(invoice)
    assert dec["network"] == "bcrt"
    assert dec["amount_sats"] == 250
    assert dec["timestamp"] == timestamp
    assert dec["tags"]["payment_hash"] == payment_hash
    assert dec["tags"]["description"] == memo
    assert dec["tags"]["expiry"] == expiry
    assert dec["tags"]["min_final_cltv_expiry_delta"] == 18
    assert dec["payee_pubkey"] == MOCK_NODE_PUBKEY
    assert dec["is_signature_valid"] is True


def test_bolt11_multipliers_and_amounts():
    """Verify exact satoshi amounts are preserved across various denominations."""
    test_amounts = [1, 25, 150, 250, 500, 1200, 5000, 12000, 100000]
    p_hash = hashlib.sha256(b"amount_test").hexdigest()

    for amt in test_amounts:
        inv = encode_bolt11(
            network="bcrt",
            amount_sats=amt,
            payment_hash_hex=p_hash,
            description=f"Payment for {amt} sats",
        )
        assert is_valid_bolt11(inv) is True
        dec = decode_bolt11(inv)
        assert dec["amount_sats"] == amt
        # Verify prefix convention starts with amount for test compatibility
        assert inv.startswith(f"lnbcrt{amt}")


def test_bolt11_checksum_tamper_detection():
    """Verify that corrupting any character causes checksum failure."""
    valid_inv = encode_bolt11(
        network="bcrt",
        amount_sats=250,
        payment_hash_hex="01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b",
        description="Tamper test",
    )
    assert is_valid_bolt11(valid_inv) is True

    # Tamper with the last character (part of checksum)
    corrupted_inv = valid_inv[:-1] + ("q" if valid_inv[-1] != "q" else "p")
    assert is_valid_bolt11(corrupted_inv) is False
    with pytest.raises(ValueError, match="Bech32 checksum verification failed"):
        decode_bolt11(corrupted_inv)


def test_mock_lightning_provider_creates_genuinely_valid_invoice():
    """Verify MockLightningProvider generates 100% parseable standard BOLT11 invoices."""
    provider = MockLightningProvider()
    req = InvoiceRequest(
        amount_sats=250,
        memo="Diagnostic telemetry micro-payment",
        expiry_seconds=1800,
        work_order_id="WO-2026-P101",
        equipment_id="P-101A",
    )

    inv = asyncio.run(provider.create_invoice(req))

    # String properties
    assert inv.payment_request.startswith("lnbcrt250")
    assert is_valid_bolt11(inv.payment_request) is True

    # Decoded properties
    dec = decode_bolt11(inv.payment_request)
    assert dec["amount_sats"] == 250
    assert dec["tags"]["payment_hash"] == inv.payment_hash
    assert dec["tags"]["expiry"] == 1800
    assert dec["tags"]["description"] == "[MOCK / SIMULATION] Diagnostic telemetry micro-payment"
    assert dec["payee_pubkey"] == MOCK_NODE_PUBKEY
    assert dec["is_signature_valid"] is True


def test_mock_lightning_provider_pays_and_decodes_external_invoice():
    """Verify MockLightningProvider can decode and pay a standard external BOLT11 invoice."""
    provider = MockLightningProvider(initial_balance_sats=10000)
    ext_hash = hashlib.sha256(b"external_payment_test").hexdigest()
    ext_inv = encode_bolt11(
        network="bcrt",
        amount_sats=450,
        payment_hash_hex=ext_hash,
        description="External vendor maintenance service",
    )

    receipt = asyncio.run(provider.pay_invoice(ext_inv))
    assert receipt.payment_hash == ext_hash
    assert receipt.amount_sats == 450
    assert receipt.status.value in ["MOCK_PAID", "PAID", "SETTLED"]
    assert provider.balance_sats == 10000 - 450
