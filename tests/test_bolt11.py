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
from backend.app.services.machine_money.exceptions import ProviderError, InvoiceExpiredError
from backend.app.services.machine_money.providers.mock import (
    MockLightningProvider,
    register_preimage,
    verify_preimage_proof,
)
from backend.app.services.machine_money.schemas import InvoiceRequest, PaymentStatus


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

    # BOLT #11 Signet compliance: signet prefix must be lntbs (BIP 173 tbs)
    signet_invoice = encode_bolt11(
        network="signet",
        amount_sats=amount,
        payment_hash_hex=payment_hash,
        description=memo,
    )
    assert signet_invoice.startswith("lntbs2500n1")
    assert is_valid_bolt11(signet_invoice) is True
    dec_signet = decode_bolt11(signet_invoice)
    assert dec_signet["network"] == "tbs"
    assert dec_signet["amount_sats"] == 250
    assert dec_signet["tags"]["payment_hash"] == payment_hash
    assert dec_signet["is_signature_valid"] is True


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


# -----------------------------------------------------------------------------
# Phase 1 Acceptance Gate Tests (PRD4 Section 1)
# -----------------------------------------------------------------------------

def test_mock_provider_rejects_malformed_invoice_zero_sats_lost():
    """Phase 1.1: Malformed invoice string must be rejected with ProviderError, 0 sats lost."""
    provider = MockLightningProvider(initial_balance_sats=50000)
    initial_balance = provider.balance_sats

    malformed_invoices = [
        "not_a_bolt11_invoice",
        "lnbcrt1",
        "lnbcrt1qqq",
        "lnbc2500n1badcharacter!!$$",
        "",
    ]

    for inv_str in malformed_invoices:
        with pytest.raises(ProviderError):
            asyncio.run(provider.pay_invoice(inv_str))
        assert provider.balance_sats == initial_balance, f"Balance was modified on {inv_str}"


def test_mock_provider_rejects_corrupt_checksum_zero_sats_lost():
    """Phase 1.1: Corrupt checksum must be rejected with ProviderError, 0 sats lost."""
    provider = MockLightningProvider(initial_balance_sats=50000)
    initial_balance = provider.balance_sats

    valid_inv = encode_bolt11(
        network="bcrt",
        amount_sats=250,
        payment_hash_hex="01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b",
        description="Tamper test",
    )
    corrupted_inv = valid_inv[:-1] + ("q" if valid_inv[-1] != "q" else "p")

    with pytest.raises(ProviderError) as exc_info:
        asyncio.run(provider.pay_invoice(corrupted_inv))

    assert "checksum" in str(exc_info.value).lower() or "structure" in str(exc_info.value).lower()
    assert provider.balance_sats == initial_balance


def test_mock_provider_rejects_valid_unregistered_invoice_zero_sats_lost():
    """Phase 1.2 & 1.4: Valid BOLT11 invoice whose payment hash is not registered must be REJECTED with 0 sats deducted."""
    provider = MockLightningProvider(initial_balance_sats=50000)
    initial_balance = provider.balance_sats

    unregistered_hash = hashlib.sha256(b"totally_unregistered_hash_unknown_to_mock").hexdigest()
    unregistered_inv = encode_bolt11(
        network="bcrt",
        amount_sats=300,
        payment_hash_hex=unregistered_hash,
        description="Unregistered invoice",
    )

    with pytest.raises(ProviderError) as exc_info:
        asyncio.run(provider.pay_invoice(unregistered_inv))

    assert "unregistered" in str(exc_info.value).lower()
    assert provider.balance_sats == initial_balance
    assert unregistered_hash not in provider._payments


def test_mock_provider_settles_registered_invoice_with_cryptographic_proof():
    """Phase 1.3 & 1.5: Valid registered invoice settles with sha256(preimage) == payment_hash verified."""
    provider = MockLightningProvider(initial_balance_sats=50000)
    initial_balance = provider.balance_sats

    req = InvoiceRequest(
        amount_sats=350,
        memo="Cryptographic proof validation payment",
        expiry_seconds=1800,
    )
    inv = asyncio.run(provider.create_invoice(req))

    receipt = asyncio.run(provider.pay_invoice(inv.payment_request))
    assert receipt.status == PaymentStatus.MOCK_PAID
    assert receipt.amount_sats == 350
    assert receipt.payment_hash == inv.payment_hash
    assert verify_preimage_proof(receipt.preimage, receipt.payment_hash) is True
    # Invariant: sha256(preimage) == payment_hash
    computed_hash = hashlib.sha256(bytes.fromhex(receipt.preimage)).hexdigest()
    assert computed_hash == receipt.payment_hash
    assert provider.balance_sats == initial_balance - 350


def test_mock_provider_rejects_mismatched_preimage_zero_sats_lost():
    """Phase 1.3: If registered preimage does not hash to invoice payment_hash, reject with ProviderError, 0 sats lost."""
    provider = MockLightningProvider(initial_balance_sats=50000)
    initial_balance = provider.balance_sats

    real_hash = hashlib.sha256(b"real_payment_payload_data").hexdigest()
    # Register an intentional preimage mismatch
    bogus_preimage = "ff" * 32
    register_preimage(real_hash, bogus_preimage)

    inv = encode_bolt11(
        network="bcrt",
        amount_sats=400,
        payment_hash_hex=real_hash,
        description="Mismatched proof test",
    )

    with pytest.raises(ProviderError) as exc_info:
        asyncio.run(provider.pay_invoice(inv))

    assert "mismatch" in str(exc_info.value).lower() or "proof" in str(exc_info.value).lower()
    assert provider.balance_sats == initial_balance
    assert real_hash not in provider._payments


def test_mock_provider_rejects_expired_invoice_zero_sats_lost():
    """Phase 1.1: Expired invoice rejected with InvoiceExpiredError / ProviderError, 0 sats lost."""
    import time
    provider = MockLightningProvider(initial_balance_sats=50000)
    initial_balance = provider.balance_sats

    registered_hash = hashlib.sha256(b"expired_registered_test").hexdigest()
    register_preimage(registered_hash, b"expired_registered_test".hex())

    # Create invoice timestamped 2 hours ago with 1 hour expiry
    past_timestamp = int(time.time()) - 7200
    expired_inv = encode_bolt11(
        network="bcrt",
        amount_sats=250,
        payment_hash_hex=registered_hash,
        description="Expired invoice test",
        timestamp=past_timestamp,
        expiry_seconds=3600,
    )

    with pytest.raises(InvoiceExpiredError):
        asyncio.run(provider.pay_invoice(expired_inv))

    assert provider.balance_sats == initial_balance
