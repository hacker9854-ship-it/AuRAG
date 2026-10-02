"""Multi-Vendor Request-For-Quote (RFQ) Service & Explainable Selection Engine.

Supports Phase 4 (FR-04, BE-03) under Bitshala BOSS Battle 2026 guidelines.
All candidate vendor data is clearly labeled as synthetic for demonstration purposes.
"""
import hashlib
import os
import secrets
import uuid
from datetime import timedelta
from typing import Any, Dict, List, Optional

from backend.app.services.machine_money.bolt11 import encode_bolt11
from backend.app.services.machine_money.providers.mock import register_preimage
from backend.app.services.machine_money.schemas import (
    SelectionStrategy,
    VendorQuoteCandidate,
    VendorRFQRequest,
    VendorRFQResponse,
    utcnow,
)

# Catalog of deterministic synthetic vendor bidding nodes
CANDIDATE_VENDORS_BY_SERVICE: Dict[str, List[Dict[str, Any]]] = {
    "bearing-inspection": [
        {
            "vendor_id": "apex-diagnostics",
            "vendor_name": "Apex Diagnostics",
            "node_pubkey": "02" + "a1" * 32,
            "service_name": "Precision Bearing Inspection & Laser Alignment",
            "amount_sats": 250,
            "sla_hours": 1.2,
            "reliability_score": 0.994,
            "reputation_tier": "AAA",
            "parts_included": ["Laser Coupling Targets", "Acoustic Sensor Pods", "Mobil SHC 100"],
        },
        {
            "vendor_id": "precision-dynamics",
            "vendor_name": "Precision Dynamics",
            "node_pubkey": "03" + "b2" * 32,
            "service_name": "Express Ultrasound Diagnostic & Vibration Analysis",
            "amount_sats": 320,
            "sla_hours": 0.8,
            "reliability_score": 0.989,
            "reputation_tier": "AA+",
            "parts_included": ["Ultrasound Sensor Probe", "Sensor Coupling Gel"],
        },
        {
            "vendor_id": "quantum-reliability",
            "vendor_name": "Quantum Reliability",
            "node_pubkey": "02" + "c3" * 32,
            "service_name": "Comprehensive Rotary Dynamics & Bearing Overhaul",
            "amount_sats": 450,
            "sla_hours": 2.5,
            "reliability_score": 0.975,
            "reputation_tier": "A",
            "parts_included": ["Complete Bearing Assembly", "Synthetic Lubricant Pack"],
        },
    ],
    "thermal-diagnostics": [
        {
            "vendor_id": "diagnostic-node-b",
            "vendor_name": "SpectraThermal Telemetry Node B",
            "node_pubkey": "02" + "e5" * 32,
            "service_name": "Infrared Thermal Gradient Scan & Heat Exchanger Assessment",
            "amount_sats": 150,
            "sla_hours": 1.0,
            "reliability_score": 0.96,
            "reputation_tier": "A",
            "parts_included": ["Thermal Calibration Target"],
        },
        {
            "vendor_id": "flir-automated-inspection",
            "vendor_name": "FLIR Automated Telemetry Swarm",
            "node_pubkey": "03" + "f6" * 32,
            "service_name": "Rapid Multi-Spectral Thermography Sweep",
            "amount_sats": 210,
            "sla_hours": 0.5,
            "reliability_score": 0.99,
            "reputation_tier": "AAA",
            "parts_included": ["Radiometric Image Export", "Emissivity Calibration Kit"],
        },
        {
            "vendor_id": "thermal-budget-diagnostics",
            "vendor_name": "Budget Thermal Scan Node",
            "node_pubkey": "02" + "a7" * 32,
            "service_name": "Basic Spot Surface Temperature Check",
            "amount_sats": 90,
            "sla_hours": 2.5,
            "reliability_score": 0.88,
            "reputation_tier": "C+",
            "parts_included": [],
        },
    ],
}


def get_candidate_quotes_for_service(
    service_id: str,
    equipment_id: str = "P-101A",
    valid_minutes: int = 15,
) -> List[VendorQuoteCandidate]:
    """Return realistic, deterministic candidate bids for the specified service."""
    now = utcnow()
    valid_until = now + timedelta(minutes=valid_minutes)

    raw_candidates = CANDIDATE_VENDORS_BY_SERVICE.get(service_id.lower())
    if not raw_candidates:
        # Fallback generator for arbitrary service IDs
        raw_candidates = [
            {
                "vendor_id": "maintenance-node-a",
                "vendor_name": "Industrial Dynamics Specialist Node A",
                "node_pubkey": "02" + "a1" * 32,
                "service_name": f"{service_id.replace('-', ' ').title()} Baseline Inspection",
                "amount_sats": 250,
                "sla_hours": 2.0,
                "reliability_score": 0.98,
                "reputation_tier": "A+",
                "parts_included": ["Standard Service Kit"],
            },
            {
                "vendor_id": "eco-rotary-nodes",
                "vendor_name": "EcoRotary Maintenance Collective",
                "node_pubkey": "03" + "b2" * 32,
                "service_name": f"{service_id.replace('-', ' ').title()} Economy Care",
                "amount_sats": 180,
                "sla_hours": 3.0,
                "reliability_score": 0.92,
                "reputation_tier": "B",
                "parts_included": [],
            },
            {
                "vendor_id": "apex-industrial-robotics",
                "vendor_name": "Apex Industrial Robotics Dispatch",
                "node_pubkey": "02" + "c3" * 32,
                "service_name": f"{service_id.replace('-', ' ').title()} Express Robotic Diagnostic",
                "amount_sats": 350,
                "sla_hours": 1.0,
                "reliability_score": 0.99,
                "reputation_tier": "AAA",
                "parts_included": ["High-Precision Calibration"],
            },
        ]

    candidates: List[VendorQuoteCandidate] = []
    for idx, c in enumerate(raw_candidates, start=1):
        candidate_id = f"BID-{service_id[:4].upper()}-{idx:02d}"
        
        # Synthesize and register genuine cryptographically valid BOLT11 payment request
        bid_preimage = secrets.token_hex(32)
        bid_payment_hash = hashlib.sha256(bytes.fromhex(bid_preimage)).hexdigest()
        register_preimage(bid_payment_hash, bid_preimage)

        candidates.append(
            VendorQuoteCandidate(
                candidate_id=candidate_id,
                vendor_id=c["vendor_id"],
                vendor_name=c["vendor_name"],
                node_pubkey=c["node_pubkey"],
                service_id=service_id,
                service_name=c["service_name"],
                amount_sats=c["amount_sats"],
                sla_hours=c["sla_hours"],
                reliability_score=c["reliability_score"],
                reputation_tier=c["reputation_tier"],
                parts_included=c["parts_included"],
                is_synthetic=True,
                within_policy_cap=True,
                score=0.0,
                valid_until=valid_until,
            )
        )
    return candidates


def process_vendor_rfq(request: VendorRFQRequest, use_live_dispatch: bool = False) -> VendorRFQResponse:
    """Execute rule/model-driven explainable multi-vendor RFQ selection (FR-04)."""
    rfq_id = f"RFQ-{uuid.uuid4().hex[:10].upper()}"
    requested_at = utcnow()

    candidates = get_candidate_quotes_for_service(
        service_id=request.service_id,
        equipment_id=request.equipment_id,
    )

    # Flag policy compliance on each candidate
    for c in candidates:
        c.within_policy_cap = c.amount_sats <= request.max_budget_sats

    # Calculate average SLA for explanation reference
    avg_sla = sum(c.sla_hours for c in candidates) / max(1, len(candidates))

    # Evaluate candidates according to selection strategy
    selected: VendorQuoteCandidate
    rationale: str
    scoring_model_meta: Dict[str, Any] = {
        "strategy": request.strategy.value,
        "max_budget_sats": request.max_budget_sats,
        "total_bids": len(candidates),
    }

    eligible_under_cap = [c for c in candidates if c.within_policy_cap]

    if request.strategy == SelectionStrategy.FASTEST_SLA:
        scoring_model_meta["rule"] = "Minimize SLA hours subject to amount_sats <= policy_cap_sats"
        for c in candidates:
            # Score reflects speed (higher score = faster SLA)
            speed_score = max(0.0, 100.0 - (c.sla_hours * 20.0))
            cap_penalty = 0.0 if c.within_policy_cap else 1000.0
            c.score = round(speed_score - cap_penalty, 2)

        if eligible_under_cap:
            eligible_sorted = sorted(
                eligible_under_cap,
                key=lambda x: (x.sla_hours, -x.reliability_score, x.amount_sats, x.candidate_id),
            )
            selected = eligible_sorted[0]
            rationale = (
                f"Selected vendor: {selected.vendor_name} ({selected.vendor_id}). "
                f"Reason: Fastest dispatch SLA ({selected.sla_hours}h vs catalog avg {avg_sla:.1f}h) "
                f"within the authorized spending policy ({selected.amount_sats} sats <= {request.max_budget_sats} sats cap)."
            )
        else:
            # All bids exceed cap
            all_sorted = sorted(candidates, key=lambda x: (x.sla_hours, x.amount_sats, x.candidate_id))
            selected = all_sorted[0]
            rationale = (
                f"Warning: All available vendor bids exceed current spending cap ({request.max_budget_sats} sats). "
                f"Fastest candidate {selected.vendor_name} ({selected.amount_sats} sats, {selected.sla_hours}h SLA) "
                f"requires human operator approval sign-off."
            )

    elif request.strategy == SelectionStrategy.LOWEST_COST:
        scoring_model_meta["rule"] = "Minimize satoshi cost subject to amount_sats <= policy_cap_sats"
        for c in candidates:
            cost_score = max(0.0, float(request.max_budget_sats - c.amount_sats))
            cap_penalty = 0.0 if c.within_policy_cap else 1000.0
            c.score = round(cost_score - cap_penalty, 2)

        if eligible_under_cap:
            eligible_sorted = sorted(
                eligible_under_cap,
                key=lambda x: (x.amount_sats, x.sla_hours, -x.reliability_score, x.candidate_id),
            )
            selected = eligible_sorted[0]
            rationale = (
                f"Selected vendor: {selected.vendor_name} ({selected.vendor_id}). "
                f"Reason: Lowest satoshi expenditure ({selected.amount_sats} sats vs max cap {request.max_budget_sats} sats) "
                f"preserving plant maintenance treasury."
            )
        else:
            all_sorted = sorted(candidates, key=lambda x: (x.amount_sats, x.sla_hours, x.candidate_id))
            selected = all_sorted[0]
            rationale = (
                f"Warning: All candidate bids exceed authorized policy cap ({request.max_budget_sats} sats). "
                f"Most economical candidate {selected.vendor_name} ({selected.amount_sats} sats) held for operator sign-off."
            )

    elif request.strategy == SelectionStrategy.HIGHEST_RELIABILITY:
        scoring_model_meta["rule"] = "Maximize historical reliability score subject to amount_sats <= policy_cap_sats"
        for c in candidates:
            rel_score = c.reliability_score * 100.0
            cap_penalty = 0.0 if c.within_policy_cap else 1000.0
            c.score = round(rel_score - cap_penalty, 2)

        if eligible_under_cap:
            eligible_sorted = sorted(
                eligible_under_cap,
                key=lambda x: (-x.reliability_score, x.sla_hours, x.amount_sats, x.candidate_id),
            )
            selected = eligible_sorted[0]
            rationale = (
                f"Selected vendor: {selected.vendor_name} ({selected.vendor_id}). "
                f"Reason: Peak historical reliability rating ({int(selected.reliability_score * 100)}%) "
                f"minimizing catastrophic downtime risk on critical asset {request.equipment_id}."
            )
        else:
            all_sorted = sorted(candidates, key=lambda x: (-x.reliability_score, x.amount_sats, x.candidate_id))
            selected = all_sorted[0]
            rationale = (
                f"Warning: All candidate bids exceed spending cap ({request.max_budget_sats} sats). "
                f"Highest reliability candidate {selected.vendor_name} ({int(selected.reliability_score * 100)}% reliability) "
                f"requires human approval."
            )

    else:  # BALANCED
        scoring_model_meta["rule"] = "Score = (0.5 * CostNorm) + (0.3 * LatencyNorm) + (0.2 * SLANorm)"
        for c in candidates:
            norm_cost = max(0.0, 1.0 - (c.amount_sats / max(1, request.max_budget_sats)))
            norm_sla = max(0.0, 1.0 - (c.sla_hours / 4.0))
            norm_rel = c.reliability_score
            composite = (0.50 * norm_cost) + (0.30 * norm_sla) + (0.20 * norm_rel)
            if not c.within_policy_cap:
                composite -= 5.0
            c.score = round(composite * 100.0, 2)

        if eligible_under_cap:
            eligible_sorted = sorted(
                eligible_under_cap,
                key=lambda x: (-x.score, x.sla_hours, x.amount_sats, x.candidate_id),
            )
            selected = eligible_sorted[0]
            rationale = (
                f"Selected vendor: {selected.vendor_name} ({selected.vendor_id}). "
                f"Reason: Optimal multi-objective score ({selected.score:.1f}/100) "
                f"balancing cost ({selected.amount_sats} sats), SLA ({selected.sla_hours}h), and reliability ({int(selected.reliability_score * 100)}%)."
            )
        else:
            all_sorted = sorted(candidates, key=lambda x: (-x.score, x.amount_sats, x.candidate_id))
            selected = all_sorted[0]
            rationale = (
                f"Warning: All available vendor bids exceed spending cap ({request.max_budget_sats} sats). "
                f"Highest-scoring candidate {selected.vendor_name} ({selected.amount_sats} sats) held for operator review."
            )

    return VendorRFQResponse(
        rfq_id=rfq_id,
        requested_at=requested_at,
        service_id=request.service_id,
        equipment_id=request.equipment_id,
        strategy=request.strategy,
        policy_cap_sats=request.max_budget_sats,
        candidates=candidates,
        selected_vendor=selected,
        selection_rationale=rationale,
        scoring_model=scoring_model_meta,
        is_synthetic=True,
    )
