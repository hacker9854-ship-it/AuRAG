"""Validate fused and reranked retrieval against known-correct answers.

A query passes when at least one expected key appears in the top five. The
graph can contain several valid related records, so exact-set equality is not
the acceptance criterion.

Usage: python -m retrieval.validate_retrieval
"""

import json
from pathlib import Path
import sys

import truststore

truststore.inject_into_ssl()

from retrieval.hybrid import retrieve
from retrieval.index_chunks import get_database, get_driver

REPO_ROOT = Path(__file__).resolve().parents[1]
GROUND_TRUTH_FILE = REPO_ROOT / "retrieval" / "ground_truth.json"


def main() -> None:
    ground_truth = json.loads(GROUND_TRUTH_FILE.read_text(encoding="utf-8"))
    driver, db = get_driver(), get_database()
    total = matched_count = 0

    try:
        with driver.session(database=db) as session:
            for qid, spec in ground_truth.items():
                expected = set(spec["expected_any"])
                got_keys = {
                    key for key, _, _ in retrieve(session, spec["query"], top_k=5)
                }
                matched = expected & got_keys
                status = "OK" if matched else "MISMATCH"
                total += 1
                matched_count += int(bool(matched))

                print(f"[{status}] {qid}: {spec['query']!r}")
                print(
                    f"    expected any of {sorted(expected)}, "
                    f"got {sorted(got_keys)}"
                )
    finally:
        driver.close()

    print(
        f"\nTotal: {matched_count}/{total} queries matched at least one "
        "expected key."
    )
    if matched_count != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
