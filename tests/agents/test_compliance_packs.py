"""Automated tests for Indian statutory industrial compliance packs."""
from agents.compliance_packs import audit_equipment_compliance


def test_factories_act_pressure_vessel_compliant():
    # Pressure vessel TK-301 with recent inspection (within 365 days)
    inspections = [
        {"clause_id": "FACT-1948-SEC-31", "days_ago": 120},
        {"clause_id": "PESO-SMPV-R18", "days_ago": 120},
    ]

    result = audit_equipment_compliance("TK-301", equipment_class="TK", inspection_records=inspections)
    assert result.audit_status == "AUDIT_PASSED"
    assert result.overdue_count == 0
    assert result.non_compliant_count == 0


def test_factories_act_pressure_vessel_overdue():
    # Pressure vessel TK-301 overdue (inspection 450 days ago > 365 max)
    inspections = [
        {"clause_id": "FACT-1948-SEC-31", "days_ago": 450},
    ]

    result = audit_equipment_compliance("TK-301", equipment_class="TK", inspection_records=inspections)
    assert result.audit_status == "AUDIT_FAILED_GAPS_FOUND"
    assert result.overdue_count >= 1

    overdue_finding = next(f for f in result.findings if f.clause_id == "FACT-1948-SEC-31")
    assert overdue_finding.status == "OVERDUE"
    assert "Section 92" in overdue_finding.penalty_summary


def test_oisd_hydrocarbon_pump_insufficient_evidence():
    # Pump P-101 checked against OISD without traceable inspection records
    result = audit_equipment_compliance("P-101", equipment_class="P", inspection_records=[])
    assert result.audit_status == "AUDIT_FAILED_GAPS_FOUND"
    assert result.non_compliant_count >= 1

    oisd_finding = next(f for f in result.findings if f.clause_id == "OISD-116-CL-4.2")
    assert oisd_finding.status == "INSUFFICIENT_EVIDENCE"
    assert "Plan 53A/B" in oisd_finding.requirement
