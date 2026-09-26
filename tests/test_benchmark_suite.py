"""Test suite for the 52-Case Golden Industrial Evaluation Benchmark."""
import json
from pathlib import Path
import pytest

from evaluation.run_benchmark import BENCHMARK_PATH, load_benchmarks, run_benchmark

REQUIRED_FIELDS = ["id", "query", "category", "equipment_tag", "acceptable_intents", "grounding_criteria"]
VALID_CATEGORIES = {"rca", "compliance", "lessons_learned", "copilot"}


def test_benchmark_dataset_integrity():
    """Verify that the benchmark file exists, contains >= 50 valid scenarios, and conforms to schema."""
    assert BENCHMARK_PATH.exists(), f"Benchmark file not found at {BENCHMARK_PATH}"
    data = load_benchmarks()
    cases = data.get("cases", [])
    
    assert len(cases) >= 50, f"Expected at least 50 benchmark cases, found {len(cases)}"
    assert data.get("total_cases") == len(cases)

    # Check schema on each case
    ids = set()
    for case in cases:
        for field in REQUIRED_FIELDS:
            assert field in case, f"Case {case.get('id')} missing required field '{field}'"
        
        cid = case["id"]
        assert cid not in ids, f"Duplicate case ID '{cid}'"
        ids.add(cid)
        
        cat = case["category"]
        assert cat in VALID_CATEGORIES, f"Case {cid} has invalid category '{cat}'"
        assert len(case["query"].strip()) > 15, f"Case {cid} has suspiciously short query"
        assert len(case["acceptable_intents"]) >= 1, f"Case {cid} has empty acceptable_intents"


def test_benchmark_category_distribution():
    """Ensure all 4 sub-agent domains have substantial test representation."""
    data = load_benchmarks()
    cases = data.get("cases", [])
    
    counts = {}
    for c in cases:
        cat = c["category"]
        counts[cat] = counts.get(cat, 0) + 1
        
    assert counts["rca"] >= 12, f"RCA has only {counts.get('rca')} cases"
    assert counts["compliance"] >= 12, f"Compliance has only {counts.get('compliance')} cases"
    assert counts["lessons_learned"] >= 10, f"Lessons Learned has only {counts.get('lessons_learned')} cases"
    assert counts["copilot"] >= 10, f"Copilot has only {counts.get('copilot')} cases"


def test_benchmark_execution_runner():
    """Verify that the benchmark runner executes all 52 cases and achieves >= 95% routing pass rate."""
    result = run_benchmark(mode="offline")
    assert result["total"] >= 50
    assert result["passed"] >= 50
    assert result["accuracy"] >= 95.0
    assert result["execution_time_s"] < 2.0
