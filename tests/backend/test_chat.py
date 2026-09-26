def test_chat_persists_evaluation_metadata_before_starting_async_scoring(monkeypatch):
    from backend.app.api import chat

    captured = {}

    monkeypatch.setattr(
        chat,
        "answer_query",
        lambda _session, query, memory_context=None, session_id=None: {
            "user_query": query,
            "intent": "rca",
            "routing_confidence": 0.9,
            "routed_agent": "rca",
            "agent_response": "Grounded answer",
            "citations": ["FE-001"],
            "graph_paths": [{"type": "FailureEvent", "id": "FE-001"}],
            "retrieved_context": [("FE-001", "evidence")],
        },
    )

    def create(session, **kwargs):
        captured["session"] = session
        captured.update(kwargs)
        return "score-1"

    class ImmediateThread:
        def __init__(self, target, args, daemon):
            captured["thread"] = {"target": target, "args": args, "daemon": daemon}

        def start(self):
            captured["started"] = True

    monkeypatch.setattr(chat, "create_score_job", create)
    monkeypatch.setattr(chat, "Thread", ImmediateThread)

    session = object()
    result = chat.chat(chat.ChatRequest(query="Why did P-101 fail?"), session=session)

    assert result["score_id"] == "score-1"
    assert captured["session"] is session
    assert captured["routed_agent"] == "rca"
    assert captured["citations"] == ["FE-001"]
    assert captured["retrieved_context"] == [("FE-001", "evidence")]
    assert captured["started"] is True


def test_chat_recalls_user_memory_without_turning_it_into_citations(monkeypatch):
    from backend.app.api import chat

    captured = {}

    class Memory:
        def recall(self, user_id, query):
            captured["recall"] = (user_id, query)
            return ["Previously investigated P-101."]

        def remember(self, **kwargs):
            captured["remember"] = kwargs
            return True

    monkeypatch.setattr(chat, "get_memory_service", lambda: Memory())
    monkeypatch.setattr(
        chat,
        "answer_query",
        lambda _session, query, memory_context=None, session_id=None: {
            "user_query": query,
            "routed_agent": "copilot",
            "agent_response": "Grounded answer",
            "citations": ["FE-001"],
            "graph_paths": [],
            "retrieved_context": [("FE-001", "evidence")],
            "received_memory": memory_context,
            "received_session": session_id,
        },
    )
    monkeypatch.setattr(chat, "create_score_job", lambda *_args, **_kwargs: "score-2")
    monkeypatch.setattr(
        chat,
        "Thread",
        lambda **_kwargs: type("Thread", (), {"start": lambda self: None})(),
    )

    result = chat.chat(
        chat.ChatRequest(query="What changed?", user_id="operator-1", session_id="session-1"),
        session=object(),
    )

    assert captured["recall"] == ("operator-1", "What changed?")
    assert result["received_memory"] == ["Previously investigated P-101."]
    assert result["received_session"] == "session-1"
    assert result["citations"] == ["FE-001"]
    assert result["memory_recalled"] == 1
    assert captured["remember"] == {
        "user_id": "operator-1",
        "session_id": "session-1",
        "query": "What changed?",
        "answer": "Grounded answer",
    }


def test_chat_remembers_successful_answer_even_without_ragas_context(monkeypatch):
    from backend.app.api import chat

    captured = {}

    class Memory:
        def recall(self, *_args):
            return []

        def remember(self, **kwargs):
            captured["remember"] = kwargs
            return True

    monkeypatch.setattr(chat, "get_memory_service", lambda: Memory())
    monkeypatch.setattr(
        chat,
        "answer_query",
        lambda _session, query, memory_context=None, session_id=None: {
            "user_query": query,
            "routed_agent": "copilot",
            "agent_response": "No plant evidence was found.",
            "citations": [],
            "graph_paths": [],
            "retrieved_context": [],
        },
    )

    result = chat.chat(
        chat.ChatRequest(query="Unknown question", user_id="operator-1", session_id="session-2"),
        session=object(),
    )

    assert result["ragas_status"] == "skipped_no_context"
    assert captured["remember"]["session_id"] == "session-2"
    assert captured["remember"]["answer"] == "No plant evidence was found."


def test_chat_score_reads_through_durable_session(monkeypatch):
    from backend.app.api import chat

    session = object()
    monkeypatch.setattr(
        chat,
        "get_score_job",
        lambda score_id, session=None: {
            "score_id": score_id,
            "session_was_used": session is not None,
        },
    )

    result = chat.chat_score("score-1", session=session)

    assert result == {"score_id": "score-1", "session_was_used": True}
