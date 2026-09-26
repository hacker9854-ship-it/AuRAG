"""Ground-truth check for all four Phase 4 agents, mirroring
retrieval/validate_retrieval.py's report format (expected_any intersection,
not exact-set diff) but checked against each agent's structured `citations`
list rather than a retrieval `key` tuple."""
import json
from pathlib import Path

import truststore

truststore.inject_into_ssl()

from agents import compliance, copilot, lessons_learned, rca
from agents.validation import require_complete
from retrieval.index_chunks import get_database, get_driver

REPO_ROOT = Path(__file__).resolve().parents[1]

_AGENTS = {
    "copilot": copilot.answer,
    "rca": rca.answer,
    "compliance": compliance.answer,
    "lessons_learned": lessons_learned.answer,
}


def main():
    ground_truth = json.loads((REPO_ROOT / "agents" / "ground_truth.json").read_text())
    driver, db = get_driver(), get_database()

    matched, total = 0, 0
    with driver.session(database=db) as session:
        for agent_name, cases in ground_truth.items():
            answer_fn = _AGENTS[agent_name]
            for qid, case in cases.items():
                total += 1
                result = answer_fn(session, case["query"])
                got = set(result["citations"])
                expected = set(case["expected_any"])
                if got & expected:
                    matched += 1
                    print(f"[OK] {agent_name}/{qid}: {sorted(got)}")
                else:
                    print(f"[MISMATCH] {agent_name}/{qid}: expected any of {sorted(expected)}, got {sorted(got)}")

    driver.close()
    print(f"\n{matched}/{total} queries matched expected citations")
    require_complete(matched, total, "Agent citation validation")


if __name__ == "__main__":
    main()
