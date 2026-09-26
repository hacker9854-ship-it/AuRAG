from retrieval.candidate_filter import (
    filter_to_explicit_anchors,
    filter_to_explicit_years,
)


def test_explicit_entity_filter_removes_cross_equipment_noise():
    candidates = {
        "P101-CHUNK": "P-101 bearing failure after missed lubrication.",
        "PSV-CHUNK": "PSV-701 calibration was overdue.",
        "FE-001": "Bearing wear caused the pump failure.",
    }

    filtered = filter_to_explicit_anchors(
        candidates,
        graph_candidates=[("FE-001", candidates["FE-001"])],
        anchors=["P-101"],
    )

    assert filtered == {
        "P101-CHUNK": candidates["P101-CHUNK"],
        "FE-001": candidates["FE-001"],
    }


def test_entity_free_query_preserves_all_hybrid_candidates():
    candidates = {
        "A": "pump failure",
        "B": "compressor trip",
    }

    assert filter_to_explicit_anchors(candidates, [], []) == candidates


def test_explicit_year_filter_removes_conflicting_dated_records():
    candidates = {
        "FE-001": "FE-001 (2025-03-14): P-101 bearing failure.",
        "FE-007": "FE-007 (2026-05-12): P-101 cavitation.",
        "PROC-1": "Pump lubrication procedure with no event date.",
    }

    assert filter_to_explicit_years(
        candidates,
        "Why did P-101 fail in March 2025?",
    ) == {
        "FE-001": candidates["FE-001"],
        "PROC-1": candidates["PROC-1"],
    }


def test_year_filter_is_inactive_without_an_explicit_query_year():
    candidates = {"A": "Failure in 2025", "B": "Failure in 2026"}

    assert filter_to_explicit_years(candidates, "Why did the pump fail?") == candidates


def test_year_filter_normalizes_two_digit_document_dates():
    candidates = {
        "OLD": "Inspection Note - 12/06/26 for P-101.",
        "MATCH": "Inspection Note - 14/03/25 for P-101.",
    }

    assert filter_to_explicit_years(
        candidates,
        "Why did P-101 fail in March 2025?",
    ) == {"MATCH": candidates["MATCH"]}
