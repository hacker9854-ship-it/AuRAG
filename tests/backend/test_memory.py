from datetime import datetime, timezone
from pathlib import Path

from backend.app.core.memory import MemoryService, _prepare_mem0_runtime_dir


class FakeClient:
    def __init__(self):
        self.search_calls = []
        self.add_calls = []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return {
            "results": [
                {
                    "memory": "Operator prefers concise summaries.",
                    "metadata": {"expires_at": "2026-08-01T00:00:00+00:00"},
                },
                {
                    "memory": "Expired preference.",
                    "metadata": {"expires_at": "2026-07-01T00:00:00+00:00"},
                },
                {"memory": "Previously investigated P-101.", "metadata": {}},
            ]
        }

    def add(self, **kwargs):
        self.add_calls.append(kwargs)
        return {"results": [{"id": "mem-1"}]}


def test_memory_recall_is_user_scoped_bounded_and_drops_expired_records():
    client = FakeClient()
    service = MemoryService(
        client=client,
        max_results=2,
        now=lambda: datetime(2026, 7, 20, tzinfo=timezone.utc),
    )

    memories = service.recall("user-1", "P-101", limit=2)

    assert memories == [
        "Operator prefers concise summaries.",
        "Previously investigated P-101.",
    ]
    assert client.search_calls[0]["filters"] == {"user_id": "user-1"}
    assert client.search_calls[0]["top_k"] == 2


def test_memory_write_carries_session_and_expiration_metadata():
    client = FakeClient()
    service = MemoryService(
        client=client,
        ttl_days=30,
        now=lambda: datetime(2026, 7, 20, tzinfo=timezone.utc),
    )

    written = service.remember(
        user_id="user-1",
        session_id="session-9",
        query="Why did P-101 fail?",
        answer="Missed lubrication caused bearing wear.",
    )

    assert written is True
    call = client.add_calls[0]
    assert call["user_id"] == "user-1"
    assert call["run_id"] == "session-9"
    assert call["metadata"]["source"] == "aurag_chat"
    assert call["metadata"]["expires_at"] == "2026-08-19T00:00:00+00:00"


def test_memory_provider_failures_do_not_break_chat():
    class BrokenClient:
        def search(self, **_kwargs):
            raise RuntimeError("provider unavailable")

        def add(self, **_kwargs):
            raise RuntimeError("provider unavailable")

    service = MemoryService(client=BrokenClient())

    assert service.recall("user-1", "query") == []
    assert service.remember("user-1", "session-1", "query", "answer") is False
    assert service.status()["status"] == "degraded"
    assert "provider unavailable" in service.status()["detail"]


def test_mem0_runtime_directory_defaults_inside_project(monkeypatch):
    monkeypatch.delenv("MEM0_DIR", raising=False)

    runtime_dir = _prepare_mem0_runtime_dir()

    assert Path(runtime_dir).parts[-2:] == (".runtime", "mem0")
