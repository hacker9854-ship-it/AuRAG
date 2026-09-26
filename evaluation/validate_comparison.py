"""Compare hybrid GraphRAG retrieval with a plain dense-only baseline.

Acceptance requires GraphRAG to pass every ground-truth query, never match
fewer expected keys than dense-only, and demonstrate at least one query-level
lift over dense-only.

Usage: python -m evaluation.validate_comparison
"""

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GROUND_TRUTH_FILE = REPO_ROOT / "retrieval" / "ground_truth.json"


def matched_expected(expected: set[str], result_keys: set[str]) -> set[str]:
    return expected & result_keys


def evaluate_comparison(
    cases: dict[str, dict[str, object]],
    graph_results: dict[str, set[str]],
    dense_results: dict[str, set[str]],
) -> list[str]:
    """Return acceptance failures from already-computed result keys."""
    failures: list[str] = []
    lift_count = 0

    for qid, spec in cases.items():
        expected = set(spec["expected_any"])
        graph_matches = matched_expected(expected, graph_results.get(qid, set()))
        dense_matches = matched_expected(expected, dense_results.get(qid, set()))

        if not graph_matches:
            failures.append(f"{qid}: GraphRAG returned no expected key")
        if len(graph_matches) < len(dense_matches):
            failures.append(
                f"{qid}: GraphRAG matched {len(graph_matches)} expected keys "
                f"but dense-only matched {len(dense_matches)}"
            )
        if graph_matches and not dense_matches:
            lift_count += 1

    if lift_count == 0:
        failures.append(
            "GraphRAG showed no query-level lift: at least one case must pass "
            "with GraphRAG and fail with dense-only"
        )
    return failures


def main() -> None:
    import truststore

    truststore.inject_into_ssl()

    from retrieval.embeddings import embed_texts
    from retrieval.hybrid import retrieve
    from retrieval.index_chunks import get_database, get_driver
    from retrieval.qdrant_store import search as dense_search

    cases = json.loads(GROUND_TRUTH_FILE.read_text(encoding="utf-8"))
    graph_results: dict[str, set[str]] = {}
    dense_results: dict[str, set[str]] = {}
    driver, db = get_driver(), get_database()

    try:
        with driver.session(database=db) as session:
            for qid, spec in cases.items():
                query = str(spec["query"])
                graph_keys = {
                    key for key, _, _ in retrieve(session, query, top_k=5)
                }
                query_vector = embed_texts([query])[0]
                dense_keys = {
                    key for key, _, _ in dense_search(query_vector, top_k=5)
                }
                graph_results[qid] = graph_keys
                dense_results[qid] = dense_keys

                expected = set(spec["expected_any"])
                graph_matches = matched_expected(expected, graph_keys)
                dense_matches = matched_expected(expected, dense_keys)
                print(
                    f"[{qid}] GraphRAG={sorted(graph_matches)}; "
                    f"dense-only={sorted(dense_matches)}"
                )
    finally:
        driver.close()

    failures = evaluate_comparison(cases, graph_results, dense_results)
    if failures:
        print("\nFAILED comparison benchmark:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)

    print(
        f"\nPASSED: GraphRAG passed all {len(cases)} cases, did not "
        "underperform dense-only, and demonstrated retrieval lift."
    )


if __name__ == "__main__":
    main()
