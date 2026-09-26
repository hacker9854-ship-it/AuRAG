"""Predictive Maintenance Intelligence Engine.

Fuses real-time OSIsoft PI telemetry streams with historical SAP PM maintenance
work-order records to calculate explainable equipment failure-risk scores and
recommend maintenance turnaround windows.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

# Engineering baseline thresholds for rotating machinery (ISO 10816-3 Class II pumps)
THRESHOLDS = {
    "vibration_de": {"nominal": 2.5, "warning": 6.5, "critical": 10.0},  # mm/s RMS
    "temperature_de": {"nominal": 65.0, "warning": 85.0, "critical": 105.0},  # °C
}


@dataclass
class RiskBreakdown:
    vibration_risk: float
    thermal_risk: float
    maintenance_penalty: float
    composite_risk: float
    health_index: float  # 0 to 100 (higher is healthier)


@dataclass
class EquipmentHealthReport:
    canonical_tag: str
    site_id: str
    health_index: float
    failure_risk: float
    recommended_window: str  # IMMEDIATE_SHUTDOWN, PLAN_WITHIN_72_HOURS, SCHEDULE_NEXT_TURNAROUND, NORMAL_MONITORING
    risk_breakdown: RiskBreakdown
    primary_failure_mode: str | None
    draft_work_order: dict[str, Any] | None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_tag": self.canonical_tag,
            "site_id": self.site_id,
            "health_index": round(self.health_index, 1),
            "failure_risk": round(self.failure_risk, 3),
            "recommended_window": self.recommended_window,
            "risk_breakdown": asdict(self.risk_breakdown),
            "primary_failure_mode": self.primary_failure_mode,
            "draft_work_order": self.draft_work_order,
            "timestamp": self.timestamp,
        }


def _calculate_dimension_risk(value: float, nominal: float, warning: float, critical: float) -> float:
    if value <= nominal:
        return 0.0
    if value >= critical:
        return 1.0
    if value <= warning:
        # Scale 0.0 to 0.5 between nominal and warning
        return 0.5 * ((value - nominal) / (warning - nominal))
    # Scale 0.5 to 1.0 between warning and critical
    return 0.5 + 0.5 * ((value - warning) / (critical - warning))


def evaluate_equipment_health(
    canonical_tag: str,
    pi_metrics: dict[str, float],
    sap_history: list[dict[str, Any]] | None = None,
    site_id: str = "plant-mumbai-01",
) -> EquipmentHealthReport:
    """Evaluate equipment failure risk by fusing real-time PI streams with SAP PM history."""
    sap_history = sap_history or []

    # 1. Evaluate Vibration Risk
    vib_val = pi_metrics.get("vibration_de", THRESHOLDS["vibration_de"]["nominal"])
    vib_cfg = THRESHOLDS["vibration_de"]
    vib_risk = _calculate_dimension_risk(vib_val, vib_cfg["nominal"], vib_cfg["warning"], vib_cfg["critical"])

    # 2. Evaluate Thermal Risk
    temp_val = pi_metrics.get("temperature_de", THRESHOLDS["temperature_de"]["nominal"])
    temp_cfg = THRESHOLDS["temperature_de"]
    temp_risk = _calculate_dimension_risk(temp_val, temp_cfg["nominal"], temp_cfg["warning"], temp_cfg["critical"])

    # 3. Evaluate SAP PM Maintenance Aging & Frequency Penalty
    # Count corrective breakdown work orders in history
    breakdowns = [wo for wo in sap_history if wo.get("order_type") in ("PM02", "M2", "CORRECTIVE")]
    breakdown_count = len(breakdowns)

    # Days since last overhaul (default 180 if unspecified)
    days_since_overhaul = 180
    for wo in sap_history:
        if wo.get("order_type") in ("PM01", "M1", "OVERHAUL"):
            days_since_overhaul = wo.get("days_ago", 180)
            break

    # Age penalty scales up after 365 days of continuous operation
    age_factor = min(0.5, max(0.0, (days_since_overhaul - 180) / 365.0))
    breakdown_factor = min(0.5, breakdown_count * 0.15)
    maintenance_penalty = min(1.0, age_factor + breakdown_factor)

    # 4. Multi-Factor Composite Risk Score (Weights: Vib 40%, Temp 35%, Maintenance History 25%)
    composite_risk = (0.40 * vib_risk) + (0.35 * temp_risk) + (0.25 * maintenance_penalty)
    health_index = max(0.0, min(100.0, 100.0 * (1.0 - composite_risk)))

    # 5. Determine Actionable Maintenance Window & Primary Failure Mode
    primary_failure_mode = None
    if vib_risk > 0.70 and temp_risk > 0.70:
        primary_failure_mode = "Bearing Cage Spall & Thermal Runaway"
    elif vib_risk > 0.60:
        primary_failure_mode = "Impeller Unbalance / Severe Mechanical Looseness"
    elif temp_risk > 0.60:
        primary_failure_mode = "Lubrication Starvation / Mechanical Seal Friction"
    elif maintenance_penalty > 0.70:
        primary_failure_mode = "End-of-Life Component Fatigue"

    if vib_val >= vib_cfg["critical"] or temp_val >= temp_cfg["critical"] or composite_risk >= 0.80:
        recommended_window = "IMMEDIATE_SHUTDOWN"
    elif composite_risk >= 0.55:
        recommended_window = "PLAN_WITHIN_72_HOURS"
    elif composite_risk >= 0.30:
        recommended_window = "SCHEDULE_NEXT_TURNAROUND"
    else:
        recommended_window = "NORMAL_MONITORING"

    # 6. Draft Work Order if attention is warranted
    draft_wo = None
    if recommended_window in ("IMMEDIATE_SHUTDOWN", "PLAN_WITHIN_72_HOURS", "SCHEDULE_NEXT_TURNAROUND"):
        priority = "1-HIGH" if recommended_window == "IMMEDIATE_SHUTDOWN" else "2-MEDIUM"
        draft_wo = {
            "canonical_tag": canonical_tag,
            "order_type": "PM02",
            "priority": priority,
            "description": f"Predictive Maintenance: {primary_failure_mode or 'Condition inspection'} on {canonical_tag}",
            "recommended_actions": [
                f"Inspect bearing DE: Current temp={temp_val}°C, Vibration={vib_val} mm/s",
                "Check lubrication oil contamination and flush lines",
                "Verify shaft alignment and dynamic balancing",
            ],
            "governance_status": "DRAFT_PENDING_APPROVAL",
        }

    breakdown = RiskBreakdown(
        vibration_risk=round(vib_risk, 3),
        thermal_risk=round(temp_risk, 3),
        maintenance_penalty=round(maintenance_penalty, 3),
        composite_risk=round(composite_risk, 3),
        health_index=round(health_index, 1),
    )

    return EquipmentHealthReport(
        canonical_tag=canonical_tag,
        site_id=site_id,
        health_index=health_index,
        failure_risk=composite_risk,
        recommended_window=recommended_window,
        risk_breakdown=breakdown,
        primary_failure_mode=primary_failure_mode,
        draft_work_order=draft_wo,
    )
