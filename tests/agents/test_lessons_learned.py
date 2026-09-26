from agents.lessons_learned import (
    _authoritative_work_orders,
    _deterministic_lessons_finding,
    _select_lessons_context,
)


def test_lessons_excludes_unreviewed_or_rejected_work_orders():
    work_orders = [
        {"id": "WO-1002", "status": "Overdue"},
        {"id": "WO-AI-1", "status": "Rejected"},
        {"id": "WO-AI-2", "status": "Draft"},
        {"id": "WO-AI-3", "status": "Approved"},
    ]

    assert [item["id"] for item in _authoritative_work_orders(work_orders)] == [
        "WO-1002",
        "WO-AI-3",
    ]


def test_lessons_missed_pm_query_keeps_only_overdue_preventive_failures():
    items = [
        (
            "FE-001",
            "bearing wear caused by an interval lapse; WO-1002 was never completed",
        ),
        (
            "FE-002",
            "intercooler fouling reduced heat transfer",
        ),
        (
            "FE-004",
            "spring fatigue combined with a missed calibration; WO-1007 was never completed",
        ),
        ("WO-1002", "scheduled lubrication"),
        ("WO-1003", "cleaned intercooler"),
        ("WO-1007", "annual calibration"),
    ]

    selected = _select_lessons_context(
        items,
        "Which failures were caused by missed preventive maintenance?",
    )

    assert [key for key, _text in selected] == [
        "FE-001",
        "FE-004",
        "WO-1002",
        "WO-1007",
    ]


def test_lessons_broad_pattern_query_uses_failure_records_without_duplicates():
    items = [
        ("FE-001", "failure one with related WO-1002"),
        ("WO-1002", "work order already summarized by FE-001"),
        ("FE-002", "failure two with related WO-1003"),
        ("WO-1003", "work order already summarized by FE-002"),
    ]

    selected = _select_lessons_context(
        items,
        "What patterns do you see across equipment failures?",
    )

    assert [key for key, _text in selected] == ["FE-001", "FE-002"]


def test_lessons_builds_explicit_missed_pm_finding():
    items = [
        (
            "FE-001",
            "FE-001 on P-101: vibration — root cause: lubrication interval "
            "lapse; WO-1002 was never completed",
        ),
        (
            "FE-004",
            "FE-004 on PSV-701: premature lift — root cause: missed annual "
            "calibration; WO-1007 was never completed",
        ),
        (
            "WO-1002",
            "WO-1002 on P-101 (Preventive, Overdue): Scheduled quarterly "
            "lubrication service",
        ),
        (
            "WO-1007",
            "WO-1007 on PSV-701 (Preventive, Overdue): Scheduled annual PSV "
            "calibration",
        ),
    ]

    result = _deterministic_lessons_finding(
        items,
        "Which failures were caused by missed preventive maintenance?",
    )

    assert result["answer"] == (
        "The failures caused by missed preventive maintenance were FE-001 on "
        "P-101 and FE-004 on PSV-701: WO-1002 (scheduled quarterly lubrication "
        "service) and WO-1007 (scheduled annual PSV calibration) were overdue."
    )
    assert result["citations"] == ["FE-001", "FE-004", "WO-1002", "WO-1007"]


def test_lessons_builds_explicit_cross_failure_pattern():
    items = [
        (
            "FE-001",
            "FE-001 on P-101: vibration — root cause: lubrication interval lapse",
        ),
        (
            "FE-003",
            "FE-003 on HX-401: fouling after exceeding the recommended cleaning interval",
        ),
        (
            "FE-004",
            "FE-004 on PSV-701: spring fatigue and a missed annual calibration",
        ),
        (
            "FE-006",
            "FE-006 on P-102: seal degradation after exceeding rated service life",
        ),
        ("FE-007", "FE-007 on P-101: cavitation from low tank level"),
    ]

    result = _deterministic_lessons_finding(
        items,
        "What patterns do you see across equipment failures?",
    )

    assert result["answer"] == (
        "The recurring pattern across equipment failures is missed or exceeded "
        "maintenance intervals: FE-001 had a lubrication lapse, FE-003 exceeded "
        "its cleaning interval, FE-004 missed annual calibration, and FE-006 "
        "exceeded rated service life."
    )
    assert result["citations"] == ["FE-001", "FE-003", "FE-004", "FE-006"]
