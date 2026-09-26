"""Indian Statutory Industrial Compliance Packs.

Encapsulates mandatory regulatory rulebooks:
- Factories Act 1948 (Pressure plant examination, hydrostatic testing)
- OISD-116 / OISD-117 / OISD-156 (Refinery fire safety, ESD interlock controls)
- PESO SMPV Rules (Pressure vessel relief valve calibration certificates)
- ISO 45001 / ISO 14001 (OH&S hazard hierarchy and CTO consent compliance)
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

# Statutory Rulebook
STATUTORY_PACKS = {
    "FACTORIES_ACT_1948": [
        {
            "clause_id": "FACT-1948-SEC-31",
            "section": "Section 31: Pressure Plant",
            "statute": "The Factories Act, 1948",
            "requirement": "Every pressure vessel/plant must undergo external inspection every 6 months and hydrostatic test every 12 months by a certified Competent Person.",
            "applicable_classes": ["TK", "HEX", "V", "BLR"],
            "max_interval_days": 365,
            "penalty": "Factories Act Section 92: Imprisonment up to 2 years or fine up to INR 1,00,000.",
        },
        {
            "clause_id": "FACT-1948-SEC-28",
            "section": "Section 28: Hoists and Lifts",
            "statute": "The Factories Act, 1948",
            "requirement": "Thorough examination of every hoist and lift at least once in every period of six months.",
            "applicable_classes": ["HST", "CRN"],
            "max_interval_days": 180,
            "penalty": "Statutory non-compliance notice by State DISH.",
        },
    ],
    "OISD_STANDARDS": [
        {
            "clause_id": "OISD-116-CL-4.2",
            "section": "Clause 4.2: Pump Containment & Isolation",
            "statute": "OISD-STD-116 (Fire Protection in Refineries)",
            "requirement": "Hydrocarbon pumps handling liquids above flashpoint must have mechanical seal barrier fluid (Plan 53A/B) and remote Emergency Shutdown (ESD) valves.",
            "applicable_classes": ["P"],
            "max_interval_days": 180,
            "penalty": "Immediate regulatory audit citation and operational suspension.",
        },
        {
            "clause_id": "OISD-156-CL-5.1",
            "section": "Clause 5.1: Safety Interlocks & Trip Systems",
            "statute": "OISD-GDN-156 (Protective Systems & Interlocks)",
            "requirement": "Bypassing safety trips or interlocks during plant operation is strictly prohibited without signed Management of Change (MOC) by Head of Operations.",
            "applicable_classes": ["P", "C", "TK", "CV"],
            "max_interval_days": None,
            "penalty": "Critical safety non-conformance finding.",
        },
    ],
    "PESO_REGULATIONS": [
        {
            "clause_id": "PESO-SMPV-R18",
            "section": "Rule 18: Pressure Relief Device Calibration",
            "statute": "Static & Mobile Pressure Vessels (Unfired) Rules",
            "requirement": "Pressure relief valves (PSVs) installed on hazardous gas/liquid vessels must be tested and calibrated annually with valid test certificate issued.",
            "applicable_classes": ["TK", "V", "HEX"],
            "max_interval_days": 365,
            "penalty": "PESO license revocation / seizure of storage facility.",
        },
    ],
}


@dataclass
class Finding:
    clause_id: str
    statute: str
    section: str
    requirement: str
    status: str  # COMPLIANT, OVERDUE, NON_COMPLIANT, INSUFFICIENT_EVIDENCE
    days_since_inspection: int | None
    penalty_summary: str
    recommendation: str


@dataclass
class ComplianceAuditResult:
    equipment_tag: str
    site_id: str
    audit_status: str  # AUDIT_PASSED, AUDIT_FAILED_GAPS_FOUND, INSUFFICIENT_EVIDENCE
    findings: list[Finding]
    overdue_count: int
    non_compliant_count: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "equipment_tag": self.equipment_tag,
            "site_id": self.site_id,
            "audit_status": self.audit_status,
            "overdue_count": self.overdue_count,
            "non_compliant_count": self.non_compliant_count,
            "findings": [asdict(f) for f in self.findings],
            "timestamp": self.timestamp,
        }


def audit_equipment_compliance(
    equipment_tag: str,
    equipment_class: str,
    inspection_records: list[dict[str, Any]],
    site_id: str = "plant-mumbai-01",
) -> ComplianceAuditResult:
    """Evaluate an equipment tag against applicable Indian industrial safety statutes."""
    findings: list[Finding] = []
    eq_class_upper = equipment_class.upper()

    # Iterate through all rulebooks
    for pack_name, clauses in STATUTORY_PACKS.items():
        for rule in clauses:
            if eq_class_upper in rule["applicable_classes"]:
                # Match against supplied maintenance/inspection records
                matched_record = None
                for rec in inspection_records:
                    if rec.get("clause_id") == rule["clause_id"] or rec.get("inspection_type") == rule["section"]:
                        matched_record = rec
                        break

                if not matched_record:
                    # If the rule is a continuous operational prohibition without a periodic interval
                    if rule["max_interval_days"] is None:
                        findings.append(Finding(
                            clause_id=rule["clause_id"],
                            statute=rule["statute"],
                            section=rule["section"],
                            requirement=rule["requirement"],
                            status="COMPLIANT",
                            days_since_inspection=None,
                            penalty_summary=rule["penalty"],
                            recommendation="No active unauthorized bypasses or MOC deviations recorded.",
                        ))
                    else:
                        # Check if general inspection date exists
                        general_rec = next((r for r in inspection_records if "days_ago" in r), None)
                        if general_rec:
                            days_ago = general_rec["days_ago"]
                            if days_ago > rule["max_interval_days"]:
                                findings.append(Finding(
                                    clause_id=rule["clause_id"],
                                    statute=rule["statute"],
                                    section=rule["section"],
                                    requirement=rule["requirement"],
                                    status="OVERDUE",
                                    days_since_inspection=days_ago,
                                    penalty_summary=rule["penalty"],
                                    recommendation=f"Schedule certified inspection immediately (exceeded by {days_ago - rule['max_interval_days']} days).",
                                ))
                            else:
                                findings.append(Finding(
                                    clause_id=rule["clause_id"],
                                    statute=rule["statute"],
                                    section=rule["section"],
                                    requirement=rule["requirement"],
                                    status="COMPLIANT",
                                    days_since_inspection=days_ago,
                                    penalty_summary=rule["penalty"],
                                    recommendation="Compliant with statutory inspection window.",
                                ))
                        else:
                            findings.append(Finding(
                                clause_id=rule["clause_id"],
                                statute=rule["statute"],
                                section=rule["section"],
                                requirement=rule["requirement"],
                                status="INSUFFICIENT_EVIDENCE",
                                days_since_inspection=None,
                                penalty_summary=rule["penalty"],
                                recommendation="No traceable test certificate found on file. Audit flag raised.",
                            ))
                else:
                    if matched_record.get("status") == "NON_COMPLIANT":
                        findings.append(Finding(
                            clause_id=rule["clause_id"],
                            statute=rule["statute"],
                            section=rule["section"],
                            requirement=rule["requirement"],
                            status="NON_COMPLIANT",
                            days_since_inspection=matched_record.get("days_ago"),
                            penalty_summary=rule["penalty"],
                            recommendation=matched_record.get("notes", "Critical safety non-conformance."),
                        ))
                    else:
                        days_ago = matched_record.get("days_ago", 0)
                        is_overdue = rule["max_interval_days"] is not None and days_ago > rule["max_interval_days"]
                        findings.append(Finding(
                            clause_id=rule["clause_id"],
                            statute=rule["statute"],
                            section=rule["section"],
                            requirement=rule["requirement"],
                            status="OVERDUE" if is_overdue else "COMPLIANT",
                            days_since_inspection=days_ago,
                            penalty_summary=rule["penalty"],
                            recommendation="Overdue test" if is_overdue else "Inspection valid.",
                        ))

    overdue = sum(1 for f in findings if f.status == "OVERDUE")
    non_comp = sum(1 for f in findings if f.status in ("NON_COMPLIANT", "INSUFFICIENT_EVIDENCE"))

    if overdue > 0 or non_comp > 0:
        overall_status = "AUDIT_FAILED_GAPS_FOUND"
    else:
        overall_status = "AUDIT_PASSED"

    return ComplianceAuditResult(
        equipment_tag=equipment_tag,
        site_id=site_id,
        audit_status=overall_status,
        findings=findings,
        overdue_count=overdue,
        non_compliant_count=non_comp,
    )
