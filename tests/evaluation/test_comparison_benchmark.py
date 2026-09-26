from evaluation.validate_comparison import evaluate_comparison


CASES = {
    "Q1": {"expected_any": ["A", "B"]},
    "Q2": {"expected_any": ["C"]},
}


def test_comparison_passes_when_graph_is_complete_and_has_lift():
    failures = evaluate_comparison(
        CASES,
        graph_results={"Q1": {"A"}, "Q2": {"C"}},
        dense_results={"Q1": {"A"}, "Q2": {"unrelated"}},
    )

    assert failures == []


def test_comparison_reports_graph_miss_and_underperformance():
    failures = evaluate_comparison(
        CASES,
        graph_results={"Q1": set(), "Q2": {"C"}},
        dense_results={"Q1": {"A"}, "Q2": {"C"}},
    )

    assert "Q1: GraphRAG returned no expected key" in failures
    assert (
        "Q1: GraphRAG matched 0 expected keys but dense-only matched 1"
        in failures
    )


def test_comparison_requires_at_least_one_graph_only_win():
    failures = evaluate_comparison(
        CASES,
        graph_results={"Q1": {"A"}, "Q2": {"C"}},
        dense_results={"Q1": {"A"}, "Q2": {"C"}},
    )

    assert any("showed no query-level lift" in failure for failure in failures)
