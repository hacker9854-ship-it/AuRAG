from agents.compliance import (
    _asks_for_requirement,
    _insufficient_evidence_finding,
    _overdue_compliance_finding,
    _requirement_finding,
    _select_compliance_context,
)


def test_compliance_context_selects_requested_clause_and_real_work_orders():
    items = [
        ("OISD-STD-132-TESTMED", "recommended testing medium for relief valves"),
        (
            "OISD-STD-132-10.2ii",
            "testing and maintenance history must be provided before calibration",
        ),
        ("FACT1948-S31", "safe working pressure must not be exceeded"),
        ("WO-1007", "scheduled annual PSV calibration"),
        ("WO-1006", "recalibrated set pressure"),
        ("WO-AI-1", "rejected generated draft about calibration"),
    ]

    selected = _select_compliance_context(
        items,
        "Is PSV-701 compliant with relief valve calibration requirements?",
    )

    assert [key for key, _text in selected] == [
        "OISD-STD-132-10.2ii",
        "WO-1007",
        "WO-1006",
    ]


def test_compliance_context_keeps_canonical_work_order_when_no_direct_match():
    items = [
        ("FACT1948-S37", "prevent explosion and exclude ignition sources"),
        ("WO-1003", "cleaned fouled intercooler tubes"),
        ("WO-AI-1", "rejected generated draft"),
    ]

    selected = _select_compliance_context(
        items,
        "Is C-201 compliant with explosion-prevention requirements?",
    )

    assert [key for key, _text in selected] == ["FACT1948-S37", "WO-1003"]


def test_requirement_questions_do_not_use_compliance_verdict_mode():
    assert _asks_for_requirement(
        "What is the relief valve calibration requirement for PSV-701?"
    )
    assert not _asks_for_requirement(
        "Is PSV-701 compliant with relief valve calibration requirements?"
    )


def test_overdue_work_order_produces_explicit_auditable_finding():
    items = [
        (
            "OISD-STD-132-10.2ii",
            "testing and maintenance history must be provided before calibration",
        ),
        ("WO-1007", "WO-1007 (2025-07-01, Preventive, Overdue): Scheduled annual PSV calibration"),
        ("WO-1006", "WO-1006 (2025-08-12, Corrective, Closed): Recalibrated set pressure"),
    ]

    result = _overdue_compliance_finding(
        items,
        "Is PSV-701 compliant with relief valve calibration requirements?",
        ["PSV-701"],
    )

    assert result == {
        "answer": (
            "PSV-701 is not compliant with relief valve calibration "
            "requirements under OISD-STD-132-10.2ii because scheduled annual "
            "PSV calibration work order WO-1007 is overdue."
        ),
        "citations": ["OISD-STD-132-10.2ii", "WO-1007"],
        "context": [
            (
                "AUDIT-FINDING",
                "PSV-701 is not compliant with relief valve calibration "
                "requirements under OISD-STD-132-10.2ii because scheduled "
                "annual PSV calibration work order WO-1007 is overdue.",
            ),
            items[0],
            items[1],
        ],
    }


def test_requirement_question_returns_exact_clause_finding():
    items = [
        (
            "OISD-STD-132-10.2ii",
            "OISD-STD-132-10.2ii (OISD-STD-132): The Testing and Maintenance "
            "History of the Safety Relief Valve must be provided to the "
            "in-house testing team prior to testing or calibration.",
        ),
        ("WO-1007", "WO-1007 (Preventive, Overdue): Annual calibration"),
    ]

    result = _requirement_finding(
        items,
        "What is the relief valve calibration requirement for PSV-701?",
        ["PSV-701"],
    )

    assert result["answer"] == (
        "The relief-valve calibration requirement for PSV-701 is to provide its "
        "testing and maintenance history to the in-house testing team before "
        "testing or calibration, as required by OISD-STD-132-10.2ii."
    )
    assert result["citations"] == ["OISD-STD-132-10.2ii"]


def test_unrelated_closed_work_order_returns_conservative_evidence_gap():
    items = [
        (
            "FACT1948-S37",
            "FACT1948-S37 (Factories Act 1948): Effective enclosure of the "
            "plant, prevention of hazardous vapour accumulation, and "
            "exclusion of ignition sources are required.",
        ),
        (
            "WO-1003",
            "WO-1003 (2025-05-03, Corrective, Closed): Cleaned fouled "
            "intercooler tubes and reset the temperature trip.",
        ),
    ]

    result = _insufficient_evidence_finding(
        items,
        "Is compressor C-201 compliant with explosion-prevention requirements?",
        ["C-201"],
    )

    assert result["answer"] == (
        "C-201 is not demonstrably compliant with explosion-prevention "
        "requirements under FACT1948-S37. WO-1003 records “Cleaned fouled "
        "intercooler tubes and reset the temperature trip”, while "
        "FACT1948-S37 requires "
        "effective enclosure of the plant, prevention of hazardous vapour "
        "accumulation, and exclusion of ignition sources are required."
    )
    assert result["citations"] == ["FACT1948-S37", "WO-1003"]
    assert result["context"][0] == ("AUDIT-FINDING", result["answer"])
