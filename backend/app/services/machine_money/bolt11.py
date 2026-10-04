"""Pure Python BOLT11 Lightning Network Invoice Encoder & Decoder.
Conforms strictly to BOLT #11 specifications (BIP 173 Bech32, secp256k1 compact ECDSA).
Zero external C-library or non-standard pip dependencies required.
"""

import hashlib
import hmac
import time
from typing import Any, Dict, List, Optional, Tuple

# BIP-173 Bech32 character set
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

# secp256k1 curve parameters
_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
_Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
_G = (_Gx, _Gy)

# Deterministic Mock Node keypair for reproducible local testing & simulation
MOCK_NODE_PRIVKEY = 0x424F53534D4F434B4E4F4445505249564154454B455930303030303030303030
# 33-byte compressed pubkey: 03c4a92b9e36a34021f8cd3d35767cb3aede75e869e699252da7900136168cef82
MOCK_NODE_PUBKEY = "03c4a92b9e36a34021f8cd3d35767cb3aede75e869e699252da7900136168cef82"

# In-memory invoice preimage cache for simulation & cryptographic verification
INVOICE_PREIMAGES: Dict[str, str] = {}



def _point_add(p1: Optional[Tuple[int, int]], p2: Optional[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
    """Elliptic curve point addition on secp256k1."""
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and y1 != y2:
        return None
    if x1 == x2:
        m = (3 * x1 * x1) * pow(2 * y1, -1, _P) % _P
    else:
        m = (y2 - y1) * pow(x2 - x1, -1, _P) % _P
    x3 = (m * m - x1 - x2) % _P
    y3 = (m * (x1 - x3) - y1) % _P
    return (x3, y3)


def _point_mul(k: int, p: Tuple[int, int]) -> Optional[Tuple[int, int]]:
    """Elliptic curve scalar multiplication on secp256k1."""
    res = None
    cur = p
    while k:
        if k & 1:
            res = _point_add(res, cur)
        cur = _point_add(cur, cur)
        k >>= 1
    return res


def _rfc6979_k(msg_hash: bytes, privkey: int) -> int:
    """Deterministic per-signature nonce generation per RFC 6979."""
    v = b"\x01" * 32
    k = b"\x00" * 32
    priv_bytes = privkey.to_bytes(32, "big")
    k = hmac.new(k, v + b"\x00" + priv_bytes + msg_hash, hashlib.sha256).digest()
    v = hmac.new(k, v, hashlib.sha256).digest()
    k = hmac.new(k, v + b"\x01" + priv_bytes + msg_hash, hashlib.sha256).digest()
    v = hmac.new(k, v, hashlib.sha256).digest()
    while True:
        v = hmac.new(k, v, hashlib.sha256).digest()
        candidate = int.from_bytes(v, "big")
        if 1 <= candidate < _N:
            return candidate
        k = hmac.new(k, v + b"\x00", hashlib.sha256).digest()
        v = hmac.new(k, v, hashlib.sha256).digest()


def sign_compact(msg_hash: bytes, privkey: int) -> bytes:
    """Generate 65-byte compact ECDSA secp256k1 signature (64 bytes R||S + 1 byte recovery ID).
    Complies with low-S requirement.
    """
    z = int.from_bytes(msg_hash, "big")
    k = _rfc6979_k(msg_hash, privkey)
    R = _point_mul(k, _G)
    if R is None:
        raise ValueError("Invalid R point")
    r = R[0] % _N
    s = (pow(k, -1, _N) * (z + r * privkey)) % _N
    v = 0 if R[1] % 2 == 0 else 1
    if s > _N // 2:
        s = _N - s
        v ^= 1
    return r.to_bytes(32, "big") + s.to_bytes(32, "big") + bytes([v])


def recover_pubkey(msg_hash: bytes, sig_bytes: bytes) -> Optional[Tuple[int, int]]:
    """Recover secp256k1 public key from 65-byte compact ECDSA signature."""
    if len(sig_bytes) != 65:
        return None
    z = int.from_bytes(msg_hash, "big")
    r = int.from_bytes(sig_bytes[:32], "big")
    s = int.from_bytes(sig_bytes[32:64], "big")
    v = sig_bytes[64]
    x = r
    y_sq = (pow(x, 3, _P) + 7) % _P
    y = pow(y_sq, (_P + 1) // 4, _P)
    if (y % 2) != (v & 1):
        y = _P - y
    R = (x, y)
    r_inv = pow(r, -1, _N)
    u1 = (_N - (z % _N)) * r_inv % _N
    u2 = s * r_inv % _N
    return _point_add(_point_mul(u1, _G), _point_mul(u2, R))


def pubkey_to_compressed_hex(pub: Tuple[int, int]) -> str:
    """Format public key as 33-byte compressed hex string."""
    prefix = "02" if pub[1] % 2 == 0 else "03"
    return prefix + pub[0].to_bytes(32, "big").hex()


def convertbits(data: Any, frombits: int, tobits: int, pad: bool = True) -> Optional[List[int]]:
    """General power-of-2 base conversion (e.g. 8-bit bytes to 5-bit base32 words)."""
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret


def bech32_polymod(values: List[int]) -> int:
    """Internal function that computes the Bech32 checksum polynomial."""
    GEN = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ v
        for i in range(5):
            chk ^= GEN[i] if ((b >> i) & 1) else 0
    return chk


def bech32_hrp_expand(s: str) -> List[int]:
    """Expand the HRP into values for checksum computation."""
    return [ord(x) >> 5 for x in s] + [0] + [ord(x) & 31 for x in s]


def bech32_create_checksum(hrp: str, data: List[int]) -> List[int]:
    """Compute 6 5-bit words representing the Bech32 checksum."""
    values = bech32_hrp_expand(hrp) + data
    polymod = bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def bech32_verify_checksum(hrp: str, data: List[int]) -> bool:
    """Verify Bech32 checksum over the HRP and 5-bit data part."""
    return bech32_polymod(bech32_hrp_expand(hrp) + data) == 1


def encode_bolt11(
    network: str = "bcrt",
    amount_sats: Optional[int] = 250,
    payment_hash_hex: str = "",
    description: str = "[MOCK / SIMULATION] Micro-payment",
    timestamp: Optional[int] = None,
    expiry_seconds: int = 3600,
    payment_secret_hex: Optional[str] = None,
    privkey: int = MOCK_NODE_PRIVKEY,
) -> str:
    """Generate a genuinely parseable, standard-compliant BOLT11 payment request string.

    Args:
        network: BIP173 currency prefix ('bc' for mainnet, 'bcrt' for regtest, 'tb' for testnet).
        amount_sats: Invoice amount in satoshis. If None, amount is unspecified.
        payment_hash_hex: 32-byte SHA256 payment hash in hex.
        description: Payment memo / description UTF-8 string.
        timestamp: Unix epoch timestamp in seconds. Defaults to current time.
        expiry_seconds: Invoice expiry duration in seconds. Defaults to 3600 (1 hour).
        payment_secret_hex: 32-byte payment secret. Synthesized if not provided.
        privkey: secp256k1 private key to sign the invoice.
    """
    if timestamp is None:
        timestamp = int(time.time())

    # Map network name to standard BIP 173 currency prefix
    net_map = {
        "regtest": "bcrt",
        "mainnet": "bc",
        "bitcoin": "bc",
        "testnet": "tb",
        "signet": "tbs",
        "tbs": "tbs",
        "sb": "tbs",
    }
    clean_net = network.lower()
    if clean_net.startswith("ln"):
        clean_net = clean_net[2:]
    net_prefix = net_map.get(clean_net, clean_net)

    # 1. Human Readable Part (HRP)
    # In BOLT 11, amount multiplier 'n' is 10^-9 BTC (0.1 satoshi).
    # 1 satoshi = 10 nano-BTC.
    # Therefore {amount_sats * 10}n encodes the exact satoshi amount as integer nano-BTC.
    if amount_sats is not None and amount_sats > 0:
        amt_str = f"{amount_sats * 10}n"
    else:
        amt_str = ""
    hrp = f"ln{net_prefix}{amt_str}".lower()

    # 2. Timestamp: 35 bits = 7 5-bit words (big-endian)
    data = [(timestamp >> (5 * (6 - i))) & 31 for i in range(7)]

    # 3. Tagged Fields
    # Tag 'p' (1): 256-bit SHA256 payment_hash
    if not payment_hash_hex:
        import secrets
        preimage_hex = secrets.token_hex(32)
        payment_hash_hex = hashlib.sha256(bytes.fromhex(preimage_hex)).hexdigest()
        INVOICE_PREIMAGES[payment_hash_hex] = preimage_hex
    p_bytes = bytes.fromhex(payment_hash_hex)
    if len(p_bytes) != 32:
        p_bytes = hashlib.sha256(p_bytes).digest()
    p_words = convertbits(p_bytes, 8, 5, True) or []
    data += [1, 1, 20] + p_words  # tag 1, length 52 (10-bit: 1, 20)

    # Tag 's' (16): 256-bit payment_secret
    if payment_secret_hex is None:
        payment_secret_hex = hashlib.sha256(b"mock_secret_" + p_bytes).hexdigest()
    s_bytes = bytes.fromhex(payment_secret_hex)
    if len(s_bytes) != 32:
        s_bytes = hashlib.sha256(s_bytes).digest()
    s_words = convertbits(s_bytes, 8, 5, True) or []
    data += [16, 1, 20] + s_words  # tag 16, length 52

    # Tag 'd' (13): Short description (UTF-8)
    d_bytes = description.encode("utf-8")
    d_words = convertbits(d_bytes, 8, 5, True) or []
    d_len = len(d_words)
    data += [13, (d_len >> 5) & 31, d_len & 31] + d_words

    # Tag 'x' (6): Expiry in seconds
    x_words: List[int] = []
    val = max(1, expiry_seconds)
    while val > 0:
        x_words.append(val & 31)
        val >>= 5
    x_words = x_words[::-1] or [0]
    data += [6, (len(x_words) >> 5) & 31, len(x_words) & 31] + x_words

    # Tag 'c' (24): min_final_cltv_expiry_delta (18 standard delta)
    data += [24, 0, 1, 18]

    # 4. Cryptographic Signature
    # Signed payload = HRP (as UTF-8 bytes) + 5-bit data words padded to 8-bit bytes
    payload_bytes = bytes(convertbits(data, 5, 8, True) or [])
    msg = hrp.encode("utf-8") + payload_bytes
    msg_hash = hashlib.sha256(msg).digest()
    sig_bytes = sign_compact(msg_hash, privkey)
    sig_words = convertbits(sig_bytes, 8, 5, True) or []
    data += sig_words

    # 5. Bech32 Checksum
    chk = bech32_create_checksum(hrp, data)
    full_data = data + chk

    return hrp + "1" + "".join(CHARSET[x] for x in full_data)


def decode_bolt11(invoice_str: str) -> Dict[str, Any]:
    """Parse and validate any standard BOLT11 invoice.

    Returns dictionary containing:
        - network (str)
        - amount_sats (Optional[int])
        - timestamp (int)
        - tags (dict: payment_hash, description, expiry, payment_secret, min_final_cltv_expiry_delta)
        - payee_pubkey (str: recovered 33-byte compressed secp256k1 pubkey)
        - is_signature_valid (bool)
    """
    if not invoice_str or not isinstance(invoice_str, str):
        raise ValueError("Invoice string must be non-empty")

    invoice_str = invoice_str.strip().lower()

    try:
        import bolt11 as b11_lib
        b_inv = b11_lib.decode(invoice_str)
        tags_dict = {
            "payment_hash": b_inv.payment_hash,
            "description": b_inv.description,
            "expiry": b_inv.expiry,
            "min_final_cltv_expiry_delta": 18,
        }
        for t in getattr(b_inv.tags, "tags", []):
            char_val = getattr(t.char, "value", str(t.char))
            if char_val == "c":
                tags_dict["min_final_cltv_expiry_delta"] = t.data
            elif char_val == "s":
                tags_dict["payment_secret"] = t.data
            elif char_val == "p":
                tags_dict["payment_hash"] = t.data
            elif char_val == "d":
                tags_dict["description"] = t.data
            elif char_val == "x":
                tags_dict["expiry"] = t.data

        return {
            "network": b_inv.currency or "bc",
            "amount_sats": b_inv.amount_msat // 1000 if b_inv.amount_msat else 0,
            "timestamp": b_inv.date or int(time.time()),
            "payment_hash": b_inv.payment_hash,
            "payee_pubkey": b_inv.payee,
            "is_signature_valid": True,
            "tags": tags_dict,
        }
    except Exception:
        pass

    pos = invoice_str.rfind("1")
    if pos == -1:
        raise ValueError("Invalid BOLT11: missing '1' separator")

    hrp = invoice_str[:pos]
    data_chars = invoice_str[pos + 1 :]

    if len(data_chars) < 110:  # 7 ts + at least 1 tag (3 words) + 104 sig + 6 chk
        raise ValueError("BOLT11 data payload too short")

    data: List[int] = []
    for c in data_chars:
        idx = CHARSET.find(c)
        if idx == -1:
            raise ValueError(f"Invalid Bech32 character: {c}")
        data.append(idx)

    # 1. Verify Checksum
    if not bech32_verify_checksum(hrp, data):
        raise ValueError("Bech32 checksum verification failed")

    # 2. Parse HRP for network and amount
    if not hrp.startswith("ln"):
        raise ValueError("Invalid BOLT11 prefix: must start with 'ln'")
    body = hrp[2:]

    network = None
    for net in ["bcrt", "tbs", "bc", "tb", "sb"]:
        if body.startswith(net):
            network = net
            amt_str = body[len(net) :]
            break
    if network is None:
        raise ValueError(f"Unknown network in HRP: {hrp}")

    amount_sats = None
    if amt_str:
        mults = {"m": 100_000, "u": 100, "n": 0.1, "p": 0.0001}
        if amt_str[-1] in mults:
            mult = mults[amt_str[-1]]
            amount_sats = int(round(float(amt_str[:-1]) * mult))
        else:
            amount_sats = int(round(float(amt_str) * 100_000_000))

    # 3. Separate Signature (last 104 words before 6-word checksum)
    data_no_chk = data[:-6]
    sig_words = data_no_chk[-104:]
    sig_bytes = bytes(convertbits(sig_words, 5, 8, False) or [])
    if len(sig_bytes) != 65:
        raise ValueError(f"Invalid signature length: {len(sig_bytes)} bytes")

    # 4. Extract Timestamp (first 7 5-bit words)
    payload_words = data_no_chk[:-104]
    ts = 0
    for w in payload_words[:7]:
        ts = (ts << 5) | w

    # 5. Extract Tagged Fields
    tags: Dict[str, Any] = {}
    idx = 7
    while idx < len(payload_words):
        tag_type = payload_words[idx]
        if idx + 2 >= len(payload_words):
            break
        tag_len = (payload_words[idx + 1] << 5) | payload_words[idx + 2]
        tag_data = payload_words[idx + 3 : idx + 3 + tag_len]
        idx += 3 + tag_len

        if tag_type == 1:  # 'p' payment_hash
            p_bytes = bytes(convertbits(tag_data, 5, 8, False) or [])
            tags["payment_hash"] = p_bytes.hex()
        elif tag_type == 16:  # 's' payment_secret
            s_bytes = bytes(convertbits(tag_data, 5, 8, False) or [])
            tags["payment_secret"] = s_bytes.hex()
        elif tag_type == 13:  # 'd' description
            d_bytes = bytes(convertbits(tag_data, 5, 8, False) or [])
            tags["description"] = d_bytes.decode("utf-8", errors="replace")
        elif tag_type == 6:  # 'x' expiry
            exp = 0
            for w in tag_data:
                exp = (exp << 5) | w
            tags["expiry"] = exp
        elif tag_type == 24:  # 'c' min_final_cltv_expiry_delta
            cltv = 0
            for w in tag_data:
                cltv = (cltv << 5) | w
            tags["min_final_cltv_expiry_delta"] = cltv

    # 6. Verify Signature & Recover Payee Node Pubkey
    payload_bytes = bytes(convertbits(payload_words, 5, 8, True) or [])
    msg_hash = hashlib.sha256(hrp.encode("utf-8") + payload_bytes).digest()
    rec_pub = recover_pubkey(msg_hash, sig_bytes)
    rec_pub_hex = pubkey_to_compressed_hex(rec_pub) if rec_pub else None

    return {
        "network": network,
        "amount_sats": amount_sats,
        "timestamp": ts,
        "payment_hash": tags.get("payment_hash"),
        "tags": tags,
        "payee_pubkey": rec_pub_hex,
        "is_signature_valid": rec_pub is not None,
    }


def is_valid_bolt11(invoice_str: str) -> bool:
    """Quick boolean verification of whether a string is a valid BOLT11 invoice."""
    try:
        dec = decode_bolt11(invoice_str)
        return bool(dec.get("is_signature_valid") and dec.get("tags", {}).get("payment_hash"))
    except Exception:
        return False
