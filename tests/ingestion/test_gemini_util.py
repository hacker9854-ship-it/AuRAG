from ingestion import gemini_util


def test_transient_gemini_failures_are_retried(monkeypatch):
    calls = []
    sleeps = []

    class Models:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            if len(calls) < 3:
                raise RuntimeError("503 UNAVAILABLE: high demand")
            return "ok"

    client = type("Client", (), {"models": Models()})()
    monkeypatch.setattr(gemini_util, "_last_call", 0.0)
    monkeypatch.setattr(gemini_util, "_MIN_INTERVAL", 0.0)
    monkeypatch.setattr(gemini_util.time, "sleep", sleeps.append)

    assert gemini_util.throttled_generate(client, prompt="test") == "ok"
    assert len(calls) == 3
    assert sleeps == [5.0, 15.0]


def test_non_transient_gemini_failure_is_not_retried(monkeypatch):
    class Models:
        def generate_content(self, **_kwargs):
            raise RuntimeError("invalid request")

    client = type("Client", (), {"models": Models()})()
    monkeypatch.setattr(gemini_util, "_last_call", 0.0)
    monkeypatch.setattr(gemini_util, "_MIN_INTERVAL", 0.0)

    try:
        gemini_util.throttled_generate(client)
    except RuntimeError as exc:
        assert "invalid request" in str(exc)
    else:
        raise AssertionError("non-transient errors must propagate")
