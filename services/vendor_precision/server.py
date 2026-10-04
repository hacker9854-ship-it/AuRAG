"""Independent Webhook Service: Precision Dynamics (Phase 2A Task 2A.6).

Exposes an independently addressable HTTP vendor bidding node on port 8102 (or configured VENDOR_PRECISION_URL).
Labeled explicitly as DEMO VENDOR NODE.
"""
import hashlib
import os
import secrets
import uuid
from datetime import timedelta
from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.services.machine_money.bolt11 import encode_bolt11
from backend.app.services.machine_money.providers.mock import register_preimage
from backend.app.services.machine_money.schemas import utcnow

app = FastAPI(
    title="Precision Dynamics Vendor Node",
    description="Independent Machine Money Demo Vendor Node (Precision Dynamics)",
    version="1.0.0",
)

VENDOR_ID = "precision-dynamics"
VENDOR_NAME = "Precision Dynamics"
NODE_PUBKEY = "03" + "b2" * 32
DEFAULT_PORT = 8102


class RFQQuoteRequest(BaseModel):
    equipment_id: str = "P-101A"
    service_id: str = "bearing-inspection"
    max_budget_sats: int = 500
    strategy: str = "FASTEST_SLA"


@app.get("/health")
def health():
    """Vendor node health status and cryptographic identity."""
    return {
        "status": "healthy",
        "vendor_id": VENDOR_ID,
        "vendor_name": VENDOR_NAME,
        "node_pubkey": NODE_PUBKEY,
        "vendor_node_type": "DEMO VENDOR NODE",
        "disclosure": "PRE-APPROVED DEMO VENDOR: Independent HTTP webhook service for machine-to-machine RFQ demonstration",
    }


@app.post("/quote")
def quote(req: RFQQuoteRequest):
    """Generate dynamic vendor quote with valid registered BOLT11 payment request."""
    now = utcnow()
    valid_until = now + timedelta(minutes=15)
    amount_sats = 320
    candidate_id = f"BID-PRECISION-{uuid.uuid4().hex[:6].upper()}"

    # Generate genuine cryptographically valid BOLT11 invoice and register preimage in mock registry
    preimage = secrets.token_hex(32)
    payment_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
    register_preimage(payment_hash, preimage)

    bolt11 = encode_bolt11(
        network="bcrt",
        amount_sats=amount_sats,
        payment_hash_hex=payment_hash,
        description=f"[DEMO VENDOR NODE] {VENDOR_NAME} Express Ultrasound Feature Extraction",
    )

    return {
        "candidate_id": candidate_id,
        "vendor_id": VENDOR_ID,
        "vendor_name": VENDOR_NAME,
        "node_pubkey": NODE_PUBKEY,
        "service_id": req.service_id,
        "service_name": "Express Ultrasound Feature Extraction & Rapid SLA",
        "amount_sats": amount_sats,
        "sla_hours": 0.8,
        "reliability_score": 0.989,
        "reputation_tier": "AA+",
        "parts_included": ["Resonant Bandpass Kurtosis Map", "Acoustic Feature Extraction", "1-Hour Critical Dispatch Window Lock"],
        "bolt11": bolt11,
        "payment_hash": payment_hash,
        "vendor_node_type": "DEMO VENDOR NODE",
        "is_synthetic": True,
        "within_policy_cap": amount_sats <= req.max_budget_sats,
        "score": 0.0,
        "valid_until": valid_until.isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("VENDOR_PRECISION_PORT", DEFAULT_PORT))
    uvicorn.run(app, host="0.0.0.0", port=port)
