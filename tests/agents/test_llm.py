from agents import llm


def test_ask_json_keeps_empty_model_citations_empty(monkeypatch):
    monkeypatch.setattr(
        llm,
        "_call_groq_json",
        lambda *_args, **_kwargs: {"answer": "insufficient context", "citations": []},
    )

    result = llm.ask_json(
        system_prompt="system",
        user_prompt="question",
        context_keys=["FE-001", "PROC-001"],
    )

    assert result["citations"] == []


def test_ask_json_drops_invalid_model_citations_without_fabricating_context_keys(monkeypatch):
    monkeypatch.setattr(
        llm,
        "_call_groq_json",
        lambda *_args, **_kwargs: {
            "answer": "unsupported",
            "citations": ["NOT-A-CONTEXT-KEY"],
        },
    )

    result = llm.ask_json(
        system_prompt="system",
        user_prompt="question",
        context_keys=["FE-001", "PROC-001"],
    )

    assert result["citations"] == []


def test_ask_json_retains_valid_model_citations(monkeypatch):
    monkeypatch.setattr(
        llm,
        "_call_groq_json",
        lambda *_args, **_kwargs: {
            "answer": "grounded",
            "citations": ["PROC-001"],
        },
    )

    result = llm.ask_json(
        system_prompt="system",
        user_prompt="question",
        context_keys=["FE-001", "PROC-001"],
    )

    assert result["citations"] == ["PROC-001"]


def test_ask_json_routes_reasoning_to_gemini_when_requested(monkeypatch):
    calls = {}
    monkeypatch.setattr(
        llm,
        "_call_gemini_json",
        lambda system, user, model: calls.update(
            system=system,
            user=user,
            model=model,
        )
        or {"answer": "grounded", "citations": ["FE-001"]},
    )

    result = llm.ask_json(
        "system",
        "question",
        ["FE-001"],
        provider="gemini",
    )

    assert result["citations"] == ["FE-001"]
    assert calls["model"] == llm.GEMINI_REASONING_MODEL


def test_lessons_queries_are_routed_deterministically_without_provider(monkeypatch):
    monkeypatch.setattr(
        llm,
        "_call_groq_json",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("provider should not be called")
        ),
    )

    assert llm.classify_intent(
        "What patterns do you see across equipment failures?"
    ) == {"intent": "lessons_learned", "confidence": 1.0}
    assert llm.classify_intent(
        "Which failures were caused by missed preventive maintenance?"
    ) == {"intent": "lessons_learned", "confidence": 1.0}
    assert llm.classify_intent(
        "What is the relief valve calibration requirement for PSV-701?"
    ) == {"intent": "compliance", "confidence": 1.0}
