"""Supervisor routing validation per PRD Section 12 Phase 5: "tested across a
broad query set spanning all four intents, including ambiguous/mixed-intent
queries." Three parts:
1. Reuses agents/ground_truth.json (its outer keys ARE the expected intent)
   for a stronger end-to-end check than Phase 4's — proves routing AND the
   downstream sub-agent answer both stay correct.
2. agents/ambiguous_queries.json — no single correct intent, so only checks
   graceful non-crash + non-empty answer (PRD Section 14's actual mitigation
   goal is a working fallback, not a guessed-right router).
3. A monkeypatched classify_intent() forcing low confidence — deterministic
   proof the confidence-floor fallback edge itself fires, since a real
   ambiguous query only exercises that edge if the classifier happens to
   return low confidence on it (it might not, even while still routing
   arguably "wrong" — that's a silent blind spot otherwise, same category as
   Phase 3's Neo4j-vector isolation gap)."""
import json
from pathlib import Path
from unittest.mock import patch

import truststore

truststore.inject_into_ssl()

from agents import supervisor
from agents.validation import require_complete
from retrieval.index_chunks import get_database, get_driver

REPO_ROOT = Path(__file__).resolve().parents[1]


def _check_ground_truth(session) -> tuple[int, int]:
    ground_truth = json.loads((REPO_ROOT / "agents" / "ground_truth.json").read_text())
    matched, total = 0, 0
    for expected_intent, cases in ground_truth.items():
        for qid, case in cases.items():
            total += 1
            # One query's crash (e.g. Groq daily-quota exhaustion mid-run) must
            # not abort the whole script — same fail-open pattern already used
            # by evaluation/validate_ragas.py's main loop.
            try:
                result = supervisor.answer(session, case["query"], score=False)
            except Exception as exc:
                print(f"[CRASHED] {expected_intent}/{qid}: {exc}")
                continue
            acceptable = case.get("acceptable_intents", [expected_intent])
            routed_ok = result["routed_agent"] in acceptable
            cited_ok = bool(set(result["citations"]) & set(case["expected_any"]))
            if routed_ok and cited_ok:
                matched += 1
                print(f"[OK] {expected_intent}/{qid}: routed={result['routed_agent']} citations={sorted(result['citations'])}")
            else:
                print(
                    f"[MISMATCH] {expected_intent}/{qid}: classified={result['intent']} "
                    f"routed={result['routed_agent']} (confidence={result['routing_confidence']:.2f}), "
                    f"citations={sorted(result['citations'])}"
                )
    return matched, total


def _check_ambiguous(session) -> None:
    cases = json.loads((REPO_ROOT / "agents" / "ambiguous_queries.json").read_text())
    for case in cases:
        result = supervisor.answer(session, case["query"], score=False)
        assert result["agent_response"], f"expected non-empty answer for ambiguous query: {case['query']}"
        print(
            f"[ambiguous] {case['query']!r} -> classified={result['intent']} "
            f"(confidence={result['routing_confidence']:.2f}) routed={result['routed_agent']}"
        )


def _check_fallback_edge(session) -> None:
    """Deterministic proof the low-confidence fallback branch fires, independent
    of whether any real query happens to trigger it. Asserts both halves: the
    classifier's original guess survives untouched in `intent` (the previous
    bug clobbered it), AND `routed_agent` shows the fallback actually fired."""
    with patch("agents.supervisor.classify_intent", return_value={"intent": "rca", "confidence": 0.3}):
        result = supervisor.answer(session, "irrelevant — classify_intent is mocked", score=False)
    assert result["intent"] == "rca", f"expected original guess 'rca' preserved in intent, got {result['intent']}"
    assert result["routed_agent"] == "copilot", f"expected fallback to copilot, got {result['routed_agent']}"
    print("[OK] fallback-edge: classifier guessed 'rca' (intent preserved) but low confidence correctly fell back to routed_agent=copilot")


def main():
    driver, db = get_driver(), get_database()
    with driver.session(database=db) as session:
        matched, total = _check_ground_truth(session)
        print(f"\n{matched}/{total} clear-intent queries routed+answered correctly\n")

        _check_ambiguous(session)
        _check_fallback_edge(session)
    driver.close()
    require_complete(matched, total, "Supervisor clear-intent validation")


if __name__ == "__main__":
    main()
