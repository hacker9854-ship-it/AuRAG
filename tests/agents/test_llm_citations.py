from agents import llm


def test_empty_model_citations_remain_empty(monkeypatch):
    monkeypatch.setattr(
        llm,
        "_call_groq_json",
        lambda *_args, **_kwargs: {
            "answer": "Insufficient context.",
            "citations": [],
        },
    )

    result = llm.ask_json("system", "question", ["FE-001", "WO-1002"])

    assert result["citations"] == []


def test_invalid_model_citations_are_removed_without_fallback(monkeypatch):
    monkeypatch.setattr(
        llm,
        "_call_groq_json",
        lambda *_args, **_kwargs: {
            "answer": "An unsupported answer.",
            "citations": ["invented", "passage text"],
        },
    )

    result = llm.ask_json("system", "question", ["FE-001"])

    assert result["citations"] == []


def test_valid_model_citations_are_retained_in_model_order(monkeypatch):
    monkeypatch.setattr(
        llm,
        "_call_groq_json",
        lambda *_args, **_kwargs: {
            "answer": "Grounded answer.",
            "citations": ["WO-1002", "invalid", "FE-001"],
        },
    )

    result = llm.ask_json("system", "question", ["FE-001", "WO-1002"])

    assert result["citations"] == ["WO-1002", "FE-001"]
