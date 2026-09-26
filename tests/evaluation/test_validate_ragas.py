from evaluation.validate_ragas import (
    retry_delay_for_reason,
    run_case_with_retries,
)


def test_case_retry_recovers_from_transport_exception():
    calls = []
    sleeps = []

    def answer_fn(_session, _query):
        calls.append("call")
        if len(calls) == 1:
            raise RuntimeError("Server disconnected")
        return {"ragas_status": "scored"}

    result = run_case_with_retries(
        object(),
        "query",
        answer_fn=answer_fn,
        max_retries=2,
        retry_delay_seconds=0.25,
        sleep_fn=sleeps.append,
    )

    assert result == {"ragas_status": "scored"}
    assert len(calls) == 2
    assert sleeps == [0.25]


def test_case_retry_recovers_from_scoring_error_status():
    results = iter(
        [
            {"ragas_status": "error"},
            {"ragas_status": "scored"},
        ]
    )

    result = run_case_with_retries(
        object(),
        "query",
        answer_fn=lambda _session, _query: next(results),
        max_retries=1,
        retry_delay_seconds=0,
        sleep_fn=lambda _seconds: None,
    )

    assert result == {"ragas_status": "scored"}


def test_case_retry_does_not_retry_low_quality_scored_result():
    calls = []

    def answer_fn(_session, _query):
        calls.append("call")
        return {
            "ragas_status": "scored",
            "ragas_scores": {"faithfulness": 0.1},
        }

    result = run_case_with_retries(
        object(),
        "query",
        answer_fn=answer_fn,
        max_retries=2,
        retry_delay_seconds=0,
        sleep_fn=lambda _seconds: None,
    )

    assert result["ragas_status"] == "scored"
    assert len(calls) == 1


def test_retry_delay_honors_provider_retry_after_duration():
    delay = retry_delay_for_reason(
        "Rate limit reached. Please try again in 6m33.984s.",
        default_seconds=2,
        max_seconds=900,
    )

    assert delay == 395


def test_retry_delay_caps_provider_wait():
    delay = retry_delay_for_reason(
        "Please try again in 2h1m4s.",
        default_seconds=2,
        max_seconds=900,
    )

    assert delay == 900
