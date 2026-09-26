"""Diffs actual graph MENTIONS against ingestion/ground_truth.json, per
document (PRD Section 12: "entity extraction accuracy checked against
manual ground truth for each path"). Run after ingesting the seed corpus.

Usage: python -m ingestion.validate_ground_truth
"""
import json
from pathlib import Path

from ingestion.pipeline import get_database, get_driver

REPO_ROOT = Path(__file__).resolve().parents[1]
GROUND_TRUTH_FILE = REPO_ROOT / "ingestion" / "ground_truth.json"


def actual_mentions(session, doc_id: str) -> tuple[set[str], set[str]]:
    equipment, person = set(), set()
    for r in session.run(
        """
        MATCH (:Document {id:$id})-[:CONTAINS]->(:Chunk)-[:MENTIONS]->(n)
        RETURN labels(n)[0] AS lbl, coalesce(n.tag_id, n.name) AS key
        """,
        id=doc_id,
    ):
        (equipment if r["lbl"] == "Equipment" else person).add(r["key"])
    return equipment, person


def main() -> None:
    ground_truth = json.loads(GROUND_TRUTH_FILE.read_text(encoding="utf-8"))
    driver, db = get_driver(), get_database()

    total_expected = total_matched = total_spurious = 0

    mismatches = 0
    try:
        with driver.session(database=db) as session:
            for doc_id, expected in ground_truth.items():
                exp_equipment = set(expected["equipment"])
                exp_person = set(expected["person"])
                got_equipment, got_person = actual_mentions(session, doc_id)

                missed = (exp_equipment | exp_person) - (got_equipment | got_person)
                spurious = (got_equipment - exp_equipment) | (got_person - exp_person)
                matched = (exp_equipment | exp_person) & (got_equipment | got_person)

                total_expected += len(exp_equipment) + len(exp_person)
                total_matched += len(matched)
                total_spurious += len(spurious)

                status = "OK" if not missed and not spurious else "MISMATCH"
                mismatches += int(status == "MISMATCH")
                print(f"[{status}] {doc_id}: {len(matched)}/{len(exp_equipment) + len(exp_person)} matched")
                if missed:
                    print(f"    missed (expected, not linked): {sorted(missed)}")
                if spurious:
                    print(f"    spurious (linked, not expected): {sorted(spurious)}")
    finally:
        driver.close()

    print(f"\nTotal: {total_matched}/{total_expected} expected mentions matched, "
          f"{total_spurious} spurious across all documents.")
    if mismatches:
        raise SystemExit(
            f"Ground-truth validation failed for {mismatches} document(s)."
        )


if __name__ == "__main__":
    main()
