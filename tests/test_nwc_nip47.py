"""Unit tests for Nostr Wallet Connect (NIP-47) in AuRAG Machine Money."""

import json
import pytest
from backend.app.services.machine_money.nwc import (
    generate_nwc_keypair,
    derive_pubkey_from_secret,
    parse_nwc_uri,
    build_nwc_uri,
    nip04_encrypt,
    nip04_decrypt,
    create_nip47_request_event,
    create_nip47_response_event,
    schnorr_sign,
    schnorr_verify,
    verify_nip47_event,
    NWCClient,
)
from backend.app.services.machine_money.bolt11 import encode_bolt11


def test_nwc_keypair_generation_and_derivation():
    priv, pub = generate_nwc_keypair()
    assert len(priv) == 64
    assert len(pub) == 64
    derived_pub = derive_pubkey_from_secret(priv)
    assert derived_pub == pub


def test_nwc_uri_parsing_and_building():
    wallet_pubkey = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    secret = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    relay = "wss://relay.damus.io"
    lud16 = "aurag-agent@bitshala.org"

    uri = build_nwc_uri(wallet_pubkey, relay, secret, lud16)
    cfg = parse_nwc_uri(uri)

    assert cfg.wallet_pubkey == wallet_pubkey
    assert cfg.relay_url == relay
    assert cfg.client_secret == secret
    assert cfg.lud16 == lud16


def test_nip04_encryption_and_decryption_roundtrip():
    priv_alice, pub_alice = generate_nwc_keypair()
    priv_bob, pub_bob = generate_nwc_keypair()

    message = json.dumps({"method": "pay_invoice", "params": {"amount": 250000}})

    # Alice encrypts to Bob
    ciphertext = nip04_encrypt(priv_alice, pub_bob, message)
    assert "?iv=" in ciphertext

    # Bob decrypts from Alice
    decrypted = nip04_decrypt(priv_bob, pub_alice, ciphertext)
    assert decrypted == message


def test_nip47_request_and_response_events():
    priv_client, pub_client = generate_nwc_keypair()
    priv_wallet, pub_wallet = generate_nwc_keypair()

    req = create_nip47_request_event(
        client_secret_hex=priv_client,
        wallet_pubkey_hex=pub_wallet,
        method="get_balance",
        params={},
    )

    assert req["kind"] == 23194
    assert req["pubkey"] == pub_client
    assert len(req["sig"]) == 128
    assert req["tags"][0] == ["p", pub_wallet]
    # Cryptographic BIP-340 verification
    assert verify_nip47_event(req) is True

    res = create_nip47_response_event(
        wallet_secret_hex=priv_wallet,
        client_pubkey_hex=pub_client,
        request_event_id=req["id"],
        result_type="get_balance",
        result={"balance": 500000},
    )

    assert res["kind"] == 23195
    assert res["pubkey"] == pub_wallet
    assert len(res["sig"]) == 128
    assert ["p", pub_client] in res["tags"]
    assert ["e", req["id"]] in res["tags"]
    # Cryptographic BIP-340 verification
    assert verify_nip47_event(res) is True


def test_bip340_schnorr_signatures():
    """Verify real BIP-340 Schnorr signatures: signing, verification, and rejection gates."""
    import hashlib

    priv_hex, pub_hex = generate_nwc_keypair()
    message = b"AuRAG Machine Money BIP-340 Signature Verification"
    digest = hashlib.sha256(message).digest()

    # 1. Sign
    sig_hex = schnorr_sign(digest, priv_hex)
    assert len(sig_hex) == 128  # 64 bytes = 128 hex chars

    # 2. Verify valid signature
    assert schnorr_verify(sig_hex, digest, pub_hex) is True

    # 3. Reject tampered digest
    tampered_digest = hashlib.sha256(b"Tampered message content").digest()
    assert schnorr_verify(sig_hex, tampered_digest, pub_hex) is False

    # 4. Reject wrong public key
    _, wrong_pub_hex = generate_nwc_keypair()
    assert schnorr_verify(sig_hex, digest, wrong_pub_hex) is False

    # 5. Reject corrupted signature bytes
    corrupted_sig = sig_hex[:126] + ("00" if sig_hex[-2:] != "00" else "ff")
    assert schnorr_verify(corrupted_sig, digest, pub_hex) is False


import asyncio


def test_nwc_client_pay_invoice_lifecycle():
    client = NWCClient()
    info = client.get_info()
    assert info["protocol"] == "NIP-47 (Nostr Wallet Connect)"
    assert "pay_invoice" in info["supported_methods"]

    # Generate valid test BOLT11
    bolt11 = encode_bolt11(amount_sats=250, description="NWC bearing repair")
    receipt = asyncio.run(client.pay_invoice(bolt11))

    assert receipt["status"] == "SETTLED"
    assert receipt["protocol"] == "NIP-47"
    assert receipt["amount_sats"] == 250
    assert len(receipt["preimage"]) == 64
    assert receipt["request_event"]["kind"] == 23194
    assert receipt["response_event"]["kind"] == 23195
    assert receipt["verification"]["relay_broadcast"] == "CONFIRMED"


def test_nwc_client_cap_enforcement():
    client = NWCClient()
    bolt11 = encode_bolt11(amount_sats=1200, description="Over-budget motor repair")

    with pytest.raises(ValueError, match="exceeds 500 sat autonomous cap"):
        asyncio.run(client.pay_invoice(bolt11, amount_sats=1200))


def test_multi_hop_lightning_routing_engine():
    from backend.app.services.machine_money.routing import MultiHopRouter

    router = MultiHopRouter()
    topo = router.get_topology()
    assert topo["total_nodes"] == 6
    assert topo["total_channels"] == 5

    # Compute 4-hop route to Apex Diagnostics for 250 sats
    route = router.compute_route(amount_sats=250, target_vendor_id="apex-diagnostics")

    assert route["destination_amount_sats"] == 250
    assert route["total_hops"] == 3
    assert len(route["path"]) == 4
    assert route["path"][0] == "AuRAG Plant Edge Gateway (P-101A)"
    assert route["path"][-1] == "Apex Diagnostics Autonomous Node"
    assert route["total_network_fees_sats"] >= 1
    assert route["sphinx_onion"]["payload_bytes"] == 1366
    assert len(route["settlement_cascade"]) == 6
    assert route["cryptographic_proof"]["sha256_verified"] is True


def test_nwc_and_routing_api_endpoints():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)

    # 1. NWC Info
    resp = client.get("/api/machine-money/nwc/info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["protocol"] == "NIP-47 (Nostr Wallet Connect)"
    assert "pay_invoice" in data["supported_methods"]

    # 2. NWC Pay
    pay_resp = client.post(
        "/api/machine-money/nwc/pay",
        json={"amount_sats": 250, "memo": "NWC bearing inspection dispatch"},
    )
    assert pay_resp.status_code == 200
    pay_data = pay_resp.json()
    assert pay_data["status"] == "SETTLED"
    assert pay_data["protocol"] == "NIP-47"
    assert pay_data["amount_sats"] == 250
    assert pay_data["verification"]["relay_broadcast"] == "CONFIRMED"

    # 3. Routing Topology
    topo_resp = client.get("/api/machine-money/routing/topology")
    assert topo_resp.status_code == 200
    topo_data = topo_resp.json()
    assert topo_data["total_nodes"] == 6

    # 4. Routing Calculate
    calc_resp = client.post(
        "/api/machine-money/routing/calculate",
        json={"amount_sats": 250, "target_vendor_id": "apex-diagnostics"},
    )
    assert calc_resp.status_code == 200
    calc_data = calc_resp.json()
    assert calc_data["total_hops"] == 3
    assert calc_data["cryptographic_proof"]["sha256_verified"] is True


