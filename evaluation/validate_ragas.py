"""Hard acceptance gate for RAGAS scores across every ground-truth answer.

Every case must complete scoring and each configured metric must meet the
project threshold. Provider failures and skipped scores are release failures.

Usage: python -m evaluation.validate_ragas
"""

import argparse
import json
import math
import os
from pathlib import Path
import re
import sys
import time

import truststore

truststore.inject_into_ssl()

from evaluation.score import PASS_THRESHOLD, classify

REPO_ROOT = Path(__file__).resolve().parents[1]
_METRICS = ("faithfulness", "context_precision", "answer_relevancy")
_CASE_MAX_RETRIES = int(os.environ.get("RAGAS_CASE_MAX_RETRIES", "2"))
_CASE_RETRY_DELAY_SECONDS = float(
    os.environ.get("RAGAS_CASE_RETRY_DELAY_SECONDS", "2")
)
_CASE_MAX_RETRY_DELAY_SECONDS = float(
    os.environ.get("RAGAS_CASE_MAX_RETRY_DELAY_SECONDS", "900")
)
_RETRY_AFTER_RE = re.compile(
    r"try again in\s+"
    r"(?:(?P<hours>\d+(?:\.\d+)?)h)?"
    r"(?:(?P<minutes>\d+(?:\.\d+)?)m)?"
    r"(?P<seconds>\d+(?:\.\d+)?)s",
    re.IGNORECASE,
)


def validate_scores(
    scores: dict[str, float],
    threshold: float = PASS_THRESHOLD,
) -> list[str]:
    """Return metric-specific failures for one scored answer."""
    failures = []
    for metric in _METRICS:
        value = scores.get(metric)
        if not isinstance(value, (int, float)):
            failures.append(f"{metric} is missing or non-numeric")
        elif value < threshold:
            failures.append(f"{metric}={value:.3f} is below {threshold:.3f}")
    return failures


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate provider-backed RAGAS scores for ground-truth cases."
    )
    parser.add_argument(
        "--case",
        action="append",
        metavar="AGENT/CASE",
        help=(
            "Run only this case (repeatable), for example --case copilot/CQ1. "
            "By default every case is evaluated."
        ),
    )
    return parser.parse_args()


def retry_delay_for_reason(
    reason: str,
    *,
    default_seconds: float,
    max_seconds: float,
) -> float:
    """Honor provider retry-after text while bounding acceptance wait time."""
    match = _RETRY_AFTER_RE.search(reason)
    if not match:
        return default_seconds
    seconds = (
        float(match.group("hours") or 0) * 3600
        + float(match.group("minutes") or 0) * 60
        + float(match.group("seconds") or 0)
    )
    # Add one second so a retry does not land on the exact quota boundary.
    return min(max_seconds, max(default_seconds, math.ceil(seconds) + 1))


def run_case_with_retries(
    session,
    query: str,
    *,
    answer_fn=None,
    max_retries: int = _CASE_MAX_RETRIES,
    retry_delay_seconds: float = _CASE_RETRY_DELAY_SECONDS,
    max_retry_delay_seconds: float = _CASE_MAX_RETRY_DELAY_SECONDS,
    sleep_fn=time.sleep,
) -> dict:
    """Retry provider/transport failures, never low-quality scored results."""
    if answer_fn is None:
        from agents.supervisor import answer as answer_fn

    last_exception: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            result = answer_fn(session, query)
        except Exception as exc:
            last_exception = exc
            result = None
            retry_reason = str(exc)
        else:
            last_exception = None
            if result.get("ragas_status") != "error":
                return result
            retry_reason = (
                result.get("ragas_detail")
                or "RAGAS status was 'error'"
            )

        if attempt == max_retries:
            if last_exception is not None:
                raise last_exception
            return result

        delay = retry_delay_for_reason(
            retry_reason,
            default_seconds=retry_delay_seconds,
            max_seconds=max_retry_delay_seconds,
        )
        print(
            f"[RETRY {attempt + 1}/{max_retries}] transient case failure: "
            f"{retry_reason}; retrying in {delay:g}s",
            flush=True,
        )
        sleep_fn(delay)

    raise AssertionError("unreachable")


def main() -> None:
    from retrieval.index_chunks import get_database, get_driver

    args = _parse_args()
    # The acceptance run may use several provider requests per case.  Expose
    # which metric is in flight so a slow provider cannot be mistaken for a
    # hung validator in CI or an operator terminal.
    os.environ["EVALUATION_PROGRESS"] = "1"
    ground_truth = json.loads(
        (REPO_ROOT / "agents" / "ground_truth.json").read_text(encoding="utf-8")
    )
    requested = set(args.case or [])
    available = {
        f"{agent_name}/{qid}"
        for agent_name, cases in ground_truth.items()
        for qid in cases
    }
    unknown = sorted(requested - available)
    if unknown:
        raise SystemExit(f"Unknown case(s): {', '.join(unknown)}")

    selected_cases = [
        (agent_name, qid, case)
        for agent_name, cases in ground_truth.items()
        for qid, case in cases.items()
        if not requested or f"{agent_name}/{qid}" in requested
    ]
    expected_total = len(selected_cases)
    print(
        f"RAGAS acceptance: running {expected_total} case(s) with "
        f"threshold {PASS_THRESHOLD:.2f}.",
        flush=True,
    )
    driver, db = get_driver(), get_database()
    totals = {metric: [] for metric in _METRICS}
    failures: list[str] = []
    scored_count = 0

    try:
        with driver.session(database=db) as session:
            for ordinal, (agent_name, qid, case) in enumerate(selected_cases, start=1):
                case_name = f"{agent_name}/{qid}"
                print(
                    f"[RUNNING {ordinal}/{expected_total}] {case_name}: "
                    f"{case['query']}",
                    flush=True,
                )
                try:
                    result = run_case_with_retries(session, case["query"])
                except Exception as exc:
                    message = f"{case_name}: answer or scoring crashed: {exc}"
                    failures.append(message)
                    print(f"[FAILED] {message}", flush=True)
                    continue

                status = result.get("ragas_status")
                if status != "scored":
                    message = (
                        f"{case_name}: RAGAS status was {status!r}, "
                        "expected 'scored'"
                    )
                    failures.append(message)
                    print(f"[FAILED] {message}", flush=True)
                    continue

                scores = result.get("ragas_scores") or {}
                score_failures = validate_scores(scores)
                if score_failures:
                    for failure in score_failures:
                        message = f"{case_name}: {failure}"
                        failures.append(message)
                        print(f"[FAILED] {message}", flush=True)
                    continue

                scored_count += 1
                for metric in _METRICS:
                    totals[metric].append(float(scores[metric]))
                classified = {
                    metric: classify(float(scores[metric]))
                    for metric in _METRICS
                }
                rendered = ", ".join(
                    f"{metric}={scores[metric]:.2f}({classified[metric]})"
                    for metric in _METRICS
                )
                print(f"[PASSED] {case_name}: {rendered}", flush=True)
    finally:
        driver.close()

    print("\nRAGAS acceptance summary:", flush=True)
    print(f"  fully passing cases: {scored_count}/{expected_total}", flush=True)
    for metric in _METRICS:
        if totals[metric]:
            average = sum(totals[metric]) / len(totals[metric])
            print(
                f"  {metric}: {average:.3f} ({classify(average)}) "
                f"over {len(totals[metric])} passing cases",
                flush=True,
            )
        else:
            print(f"  {metric}: no passing scores", flush=True)

    if failures or scored_count != expected_total:
        print(f"\nFAILED: {len(failures)} acceptance issue(s).", flush=True)
        sys.exit(1)

    print(
        f"\nPASSED: all {expected_total} cases scored and every metric met "
        f"the {PASS_THRESHOLD:.2f} threshold.",
        flush=True,
    )


if __name__ == "__main__":
    main()
