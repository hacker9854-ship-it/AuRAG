"""Live acceptance check for mem0 cross-session recall.

This deliberately stubs plant retrieval and answer generation so the check
isolates mem0. It still exercises the real FastAPI chat route and
MemoryService adapter, including the write-after-answer behavior.
"""

from __future__ import annotations

import os
import time
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.api import chat
from backend.app.core import memory
from backend.app.core.neo4j import get_session
from backend.app.main import app


def _deterministic_answer(
    _session,
    query: str,
    memory_context: list[str] | None = None,
    session_id: str | None = None,
) -> dict:
    return {
        "user_query": query,
        "intent": "copilot",
        "routing_confidence": 1.0,
        "routed_agent": "copilot",
        "agent_response": "Acknowledged.",
        "citations": [],
        "graph_paths": [],
        "retrieved_context": [],
        "observed_memory": memory_context or [],
    }


def _wait_for_marker(service, user_id: str, marker: str) -> list[str]:
    for _ in range(15):
        recalled = service.recall(user_id, marker, limit=5)
        if any(marker in item for item in recalled):
            return recalled
        time.sleep(2)
    return []


def main() -> None:
    proof_id = os.environ.get("PROOF_ID") or uuid4().hex
    user_id = f"aurag-mem0-proof-user-{proof_id}"
    other_user_id = f"aurag-mem0-proof-other-{proof_id}"
    session_a = f"aurag-mem0-proof-session-a-{proof_id}"
    session_b = f"aurag-mem0-proof-session-b-{proof_id}"
    session_c = f"aurag-mem0-proof-session-c-{proof_id}"
    marker = f"AURAG-MEM0-{proof_id}"

    memory._service = None
    chat.answer_query = _deterministic_answer
    app.dependency_overrides[get_session] = lambda: object()

    client = TestClient(app)
    service = memory.get_memory_service()
    status = service.status()
    if status.get("status") != "up":
        raise RuntimeError(f"mem0 is not ready: {status}")

    try:
        first = client.post(
            "/api/chat",
            json={
                "query": (
                    "Remember this exact verification marker for a later "
                    f"session: {marker}"
                ),
                "user_id": user_id,
                "session_id": session_a,
            },
        )
        first.raise_for_status()
        first_body = first.json()
        assert first_body["session_id"] == session_a
        assert first_body["memory_recalled"] == 0

        stored = _wait_for_marker(service, user_id, marker)
        assert any(marker in item for item in stored), (
            "mem0 did not return the marker after storage"
        )

        recall_query = (
            "What verification marker did I provide earlier? "
            "It begins with AURAG-MEM0."
        )
        second = client.post(
            "/api/chat",
            json={
                "query": recall_query,
                "user_id": user_id,
                "session_id": session_b,
            },
        )
        second.raise_for_status()
        second_body = second.json()
        assert session_a != session_b
        assert second_body["session_id"] == session_b
        assert second_body["memory_recalled"] >= 1
        assert any(
            marker in item for item in second_body["observed_memory"]
        )

        isolated = client.post(
            "/api/chat",
            json={
                "query": recall_query,
                "user_id": other_user_id,
                "session_id": session_c,
            },
        )
        isolated.raise_for_status()
        isolated_body = isolated.json()
        assert isolated_body["memory_recalled"] == 0
        assert not isolated_body["observed_memory"]

        print(
            {
                "status": "PASS",
                "different_sessions": True,
                "memory_recalled": second_body["memory_recalled"],
                "marker_observed": True,
                "other_user_isolated": True,
            }
        )
    finally:
        app.dependency_overrides.clear()
        if service.client is not None:
            for temporary_user in (user_id, other_user_id):
                try:
                    service.client.delete_users(user_id=temporary_user)
                except Exception:
                    pass


if __name__ == "__main__":
    main()
