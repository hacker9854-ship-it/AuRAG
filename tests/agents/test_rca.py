from agents.rca import _select_rca_context


def test_rca_context_keeps_only_the_dated_incident_and_direct_evidence():
    items = [
        ("FE-007", "FE-007 (2026-02-11): P-101 cavitation"),
        (
            "FE-001",
            "FE-001 (2025-03-14): bearing wear caused by missed WO-1002",
        ),
        ("WO-AI-ABC", "WO-AI-ABC (2026-07-21, Corrective, Rejected): draft"),
        ("WO-1002", "WO-1002 (2025-02-01, Preventive, Overdue): lubrication"),
        ("WO-1001", "WO-1001 (2025-03-15, Corrective, Closed): bearing replacement"),
        ("PROC-001", "PROC-001 v2.1: Pump Preventive Maintenance SOP"),
        ("DOC-SCAN-001-C001", "2026 inspection note for P-101"),
        (
            "DOC-LOG-001-C002",
            "FE-001 — P-101 Drive-End Bearing Failure (2025-03-14). "
            "WO-1002 was overdue. Corrective Action: WO-1001.",
        ),
        ("DOC-SOP-001-C001", "P-101 maintenance manual effective 2025-01-05"),
    ]

    selected = _select_rca_context(
        items,
        "Why did P-101 fail in March 2025?",
    )

    assert [key for key, _text in selected] == [
        "FE-001",
        "WO-1002",
        "WO-1001",
        "DOC-LOG-001-C002",
    ]


def test_rca_context_uses_query_aligned_log_to_disambiguate_multiple_failures():
    items = [
        ("FE-001", "FE-001: bearing wear caused by missed WO-1002"),
        ("FE-002", "FE-002: high discharge temperature caused by fouling"),
        ("WO-1002", "WO-1002: pump lubrication"),
        ("WO-1003", "WO-1003: clean compressor intercooler"),
        (
            "DOC-LOG-001-C002",
            "FE-001 — P-101 bearing failure. WO-1002 was overdue.",
        ),
        (
            "DOC-LOG-001-C003",
            "FE-002 — compressor C-201 tripped on high discharge temperature. "
            "Corrective Action: WO-1003.",
        ),
    ]

    selected = _select_rca_context(
        items,
        "Why did compressor C-201 trip on high discharge temperature?",
    )

    assert [key for key, _text in selected] == [
        "FE-002",
        "WO-1003",
        "DOC-LOG-001-C003",
    ]


def test_rca_context_does_not_treat_a_procedure_title_as_evidence():
    items = [
        ("FE-001", "FE-001: bearing wear caused by missed WO-1002"),
        ("WO-1002", "WO-1002: quarterly lubrication was overdue"),
        ("PROC-001", "PROC-001 v2.1: Pump Preventive Maintenance SOP"),
    ]

    selected = _select_rca_context(items, "What caused the P-101 failure?")

    assert [key for key, _text in selected] == ["FE-001", "WO-1002"]
