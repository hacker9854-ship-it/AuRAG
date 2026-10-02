"""Industrial economics and downtime risk mitigation model for Machine Money (Phase 5, Task 5.2).
Provides transparent, versioned calculations based on inspectable synthetic industrial plant assumptions.
"""
from datetime import datetime, timezone
import logging
from typing import Dict, Optional

from backend.app.services.machine_money.schemas import (
    IndustrialEconomicsModel,
    IndustrialEconomicsRequest,
    IndustrialPlantAssumptions,
    utcnow,
)

logger = logging.getLogger(__name__)

CALCULATION_VERSION = "v2026.1-industrial-m2m"
ESTIMATED_MARKER = "ESTIMATED_SYNTHETIC_MODEL"
SYNTHETIC_DATA_BASIS = "Synthetic plant model (Petrochemical refining unit P-101A)"

# Catalog of baseline synthetic equipment assumptions stored separately per PRD §14 / Task 5.2
PLANT_ASSUMPTIONS_REGISTRY: Dict[str, IndustrialPlantAssumptions] = {
    "P-101A": IndustrialPlantAssumptions(
        plant_id="plant-mumbai-01",
        equipment_tag="P-101A",
        equipment_name="Heavy Crude Distillation Charge Pump P-101A",
        criticality_tier="TIER_1_CRITICAL",
        hourly_downtime_cost_usd=260000.0,
        unmitigated_downtime_hours=4.5,
        catastrophic_failure_probability=0.85,
        manual_procurement_hours=4.2,
        autonomous_m2m_dispatch_seconds=2.1,
        default_intervention_sats=250,
        btc_fiat_usd_rate=65000.0,
        data_basis="Synthetic plant model (Petrochemical refining unit P-101A)",
        assumptions_version="2026.1-synthetic-p101a",
    ),
    "K-201": IndustrialPlantAssumptions(
        plant_id="plant-mumbai-01",
        equipment_tag="K-201",
        equipment_name="Flash Gas Centrifugal Compressor K-201",
        criticality_tier="TIER_1_CRITICAL",
        hourly_downtime_cost_usd=320000.0,
        unmitigated_downtime_hours=6.0,
        catastrophic_failure_probability=0.90,
        manual_procurement_hours=5.5,
        autonomous_m2m_dispatch_seconds=2.4,
        default_intervention_sats=400,
        btc_fiat_usd_rate=65000.0,
        data_basis="Synthetic plant model (Compression trains K-201)",
        assumptions_version="2026.1-synthetic-k201",
    ),
    "T-301": IndustrialPlantAssumptions(
        plant_id="plant-mumbai-01",
        equipment_tag="T-301",
        equipment_name="Steam Turbogenerator Auxiliary Feed T-301",
        criticality_tier="TIER_2_ESSENTIAL",
        hourly_downtime_cost_usd=195000.0,
        unmitigated_downtime_hours=3.5,
        catastrophic_failure_probability=0.80,
        manual_procurement_hours=3.8,
        autonomous_m2m_dispatch_seconds=1.9,
        default_intervention_sats=220,
        btc_fiat_usd_rate=65000.0,
        data_basis="Synthetic plant model (Power cogeneration T-301)",
        assumptions_version="2026.1-synthetic-t301",
    ),
}


def get_plant_assumptions(equipment_tag: str = "P-101A") -> IndustrialPlantAssumptions:
    """Retrieve distinct, versioned plant baseline assumptions for equipment tag."""
    tag_clean = (equipment_tag or "P-101A").upper().strip()
    if tag_clean in PLANT_ASSUMPTIONS_REGISTRY:
        return PLANT_ASSUMPTIONS_REGISTRY[tag_clean]
    # Default to P-101A baseline with tag customized
    base = PLANT_ASSUMPTIONS_REGISTRY["P-101A"]
    return IndustrialPlantAssumptions(
        plant_id=base.plant_id,
        equipment_tag=tag_clean,
        equipment_name=f"Industrial Rotating Asset {tag_clean}",
        criticality_tier=base.criticality_tier,
        hourly_downtime_cost_usd=base.hourly_downtime_cost_usd,
        unmitigated_downtime_hours=base.unmitigated_downtime_hours,
        catastrophic_failure_probability=base.catastrophic_failure_probability,
        manual_procurement_hours=base.manual_procurement_hours,
        autonomous_m2m_dispatch_seconds=base.autonomous_m2m_dispatch_seconds,
        default_intervention_sats=base.default_intervention_sats,
        btc_fiat_usd_rate=base.btc_fiat_usd_rate,
        data_basis=f"Synthetic plant model (Parameterized for {tag_clean})",
        assumptions_version=base.assumptions_version,
    )


def calculate_industrial_economics(
    req: Optional[IndustrialEconomicsRequest] = None,
) -> IndustrialEconomicsModel:
    """Task 5.2: Execute transparent, versioned industrial economics calculation with explicit assumptions."""
    payload = req or IndustrialEconomicsRequest()
    assumptions = get_plant_assumptions(payload.equipment_tag)

    # Allow custom caller overrides while preserving default assumption traceability
    hourly_rate = (
        payload.hourly_downtime_cost_usd
        if payload.hourly_downtime_cost_usd is not None
        else assumptions.hourly_downtime_cost_usd
    )
    downtime_hours = (
        payload.unmitigated_downtime_hours
        if payload.unmitigated_downtime_hours is not None
        else assumptions.unmitigated_downtime_hours
    )
    intervention_sats = (
        payload.intervention_cost_sats
        if payload.intervention_cost_sats is not None
        else assumptions.default_intervention_sats
    )

    # 1. Gross Downtime Exposure = Avoided Outage Hours * Hourly Outage Loss
    gross_exposure_usd = round(downtime_hours * hourly_rate, 2)

    # 2. Risk-Weighted Exposure = Gross Exposure * Unmitigated Failure Probability
    risk_weighted_usd = round(gross_exposure_usd * assumptions.catastrophic_failure_probability, 2)

    # 3. Intervention Cost in USD (sats converted at spot estimate)
    # 1 sat = (btc_fiat_usd_rate / 100,000,000) USD
    sat_usd_rate = assumptions.btc_fiat_usd_rate / 100_000_000.0
    intervention_usd = round(intervention_sats * sat_usd_rate, 4)

    # 4. Net Value Preserved = Gross Exposure - Intervention Cost
    net_value_preserved = round(gross_exposure_usd - intervention_usd, 2)

    # 5. Economic Protection Multiple (Ratio of value saved vs micro-payment spent)
    protection_mult = (
        round(gross_exposure_usd / intervention_usd, 1)
        if intervention_usd > 0
        else 0.0
    )

    # 6. Response Lead Time Delta (Manual PO procurement cycle vs Autonomous M2M dispatch)
    lead_time_saved = round(
        assumptions.manual_procurement_hours - (assumptions.autonomous_m2m_dispatch_seconds / 3600.0),
        2,
    )

    return IndustrialEconomicsModel(
        is_estimated=True,
        estimated_marker=ESTIMATED_MARKER,
        calculation_version=CALCULATION_VERSION,
        equipment_tag=assumptions.equipment_tag,
        equipment_name=assumptions.equipment_name,
        downtime_hours_avoided=downtime_hours,
        hourly_downtime_cost_usd=hourly_rate,
        estimated_downtime_exposure_usd=gross_exposure_usd,
        risk_weighted_exposure_usd=risk_weighted_usd,
        intervention_cost_sats=intervention_sats,
        intervention_cost_usd=intervention_usd,
        net_value_preserved_usd=net_value_preserved,
        protection_multiple=protection_mult,
        lead_time_saved_hours=lead_time_saved,
        assumptions=assumptions,
        formula="Net Value Preserved = (Avoided Downtime Hours * Hourly Outage Rate) - Intervention Cost USD",
        risk_weighted_formula="Risk-Weighted Exposure = Gross Exposure * Failure Probability Factor",
        data_basis=assumptions.data_basis,
        transparency_notes=(
            "Modelled estimate based on synthetic industrial plant assumptions for hackathon demonstration. "
            "All assumptions and formulas are inspectable and customizable."
        ),
        computed_at=utcnow(),
    )
