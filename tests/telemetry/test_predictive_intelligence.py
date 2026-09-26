"""Automated tests for predictive maintenance intelligence (OSIsoft PI + SAP PM fusion)."""
from telemetry.predictive_intelligence import evaluate_equipment_health


def test_evaluate_equipment_health_normal():
    pi_metrics = {
        "vibration_de": 2.2,  # Normal < 2.5
        "temperature_de": 62.0,  # Normal < 65.0
    }
    sap_history = [
        {"order_type": "PM01", "days_ago": 60},  # Recently overhauled
    ]

    report = evaluate_equipment_health("P-101", pi_metrics, sap_history)
    assert report.recommended_window == "NORMAL_MONITORING"
    assert report.health_index > 80.0
    assert report.failure_risk < 0.20
    assert report.draft_work_order is None


def test_evaluate_equipment_health_plan_within_72_hours():
    pi_metrics = {
        "vibration_de": 6.8,  # Warning > 6.5
        "temperature_de": 88.0,  # Warning > 85.0
    }
    sap_history = [
        {"order_type": "PM02", "days_ago": 30},  # Recent corrective breakdown
        {"order_type": "PM02", "days_ago": 90},
    ]

    report = evaluate_equipment_health("P-101", pi_metrics, sap_history)
    assert report.recommended_window in ("PLAN_WITHIN_72_HOURS", "SCHEDULE_NEXT_TURNAROUND")
    assert report.failure_risk >= 0.40
    assert report.draft_work_order is not None
    assert report.draft_work_order["canonical_tag"] == "P-101"
    assert report.draft_work_order["governance_status"] == "DRAFT_PENDING_APPROVAL"


def test_evaluate_equipment_health_immediate_shutdown():
    pi_metrics = {
        "vibration_de": 11.2,  # Critical > 10.0
        "temperature_de": 108.5,  # Critical > 105.0
    }
    sap_history = [
        {"order_type": "PM02", "days_ago": 10},
        {"order_type": "PM01", "days_ago": 700},  # Overdue for overhaul
    ]

    report = evaluate_equipment_health("P-101", pi_metrics, sap_history)
    assert report.recommended_window == "IMMEDIATE_SHUTDOWN"
    assert report.failure_risk > 0.80
    assert report.health_index < 20.0
    assert report.primary_failure_mode == "Bearing Cage Spall & Thermal Runaway"
    assert report.draft_work_order["priority"] == "1-HIGH"
