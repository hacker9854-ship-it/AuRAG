"""Fail-open mem0 adapter for user-scoped, cross-session chat memory."""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _prepare_mem0_runtime_dir() -> str:
    """Keep mem0's local telemetry/config state in an explicitly writable path."""
    default_dir = Path(__file__).resolve().parents[3] / ".runtime" / "mem0"
    return os.environ.setdefault("MEM0_DIR", str(default_dir))


class MemoryService:
    def __init__(
        self,
        *,
        client=None,
        ttl_days: int = 30,
        max_results: int = 5,
        now: Callable[[], datetime] = _utc_now,
    ):
        self.ttl_days = ttl_days
        self.max_results = max_results
        self._now = now
        self._last_error: str | None = None

        if client is not None:
            self.client = client
            self._configured = True
            return

        api_key = os.environ.get("MEM0_API_KEY")
        if not api_key:
            self.client = None
            self._configured = False
            return

        try:
            _prepare_mem0_runtime_dir()
            from mem0 import MemoryClient

            self.client = MemoryClient(api_key=api_key)
            self._configured = True
        except Exception as exc:
            self.client = None
            self._configured = True
            self._last_error = str(exc)

    def _not_expired(self, metadata: dict) -> bool:
        value = metadata.get("expires_at")
        if not value:
            return True
        try:
            expires_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return False
        return expires_at > self._now()

    def recall(self, user_id: str, query: str, limit: int | None = None) -> list[str]:
        if not self.client or not user_id.strip() or not query.strip():
            return []

        limit = max(1, min(limit or self.max_results, self.max_results))
        try:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self.client.search,
                    query=query,
                    filters={"user_id": user_id},
                    top_k=limit,
                )
                response = future.result(timeout=2.0)

            records = response.get("results", response) if isinstance(response, dict) else response
            memories = []
            for record in records or []:
                if not isinstance(record, dict) or not self._not_expired(record.get("metadata") or {}):
                    continue
                text = record.get("memory") or record.get("text")
                if text and text not in memories:
                    memories.append(text)
                if len(memories) >= limit:
                    break
            self._last_error = None
            return memories
        except Exception as exc:
            self._last_error = str(exc)
            return []

    def remember(
        self,
        user_id: str,
        session_id: str,
        query: str,
        answer: str,
    ) -> bool:
        if not self.client or not user_id.strip() or not query.strip() or not answer.strip():
            return False

        expires_at = (self._now() + timedelta(days=self.ttl_days)).isoformat()
        from threading import Thread

        def _bg_remember():
            try:
                self.client.add(
                    messages=[
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": answer},
                    ],
                    user_id=user_id,
                    run_id=session_id,
                    metadata={
                        "source": "aurag_chat",
                        "session_id": session_id,
                        "expires_at": expires_at,
                    },
                )
            except Exception as exc:
                self._last_error = str(exc)

        Thread(target=_bg_remember, daemon=True).start()
        return True


    def status(self) -> dict[str, str]:
        if not self._configured:
            return {"status": "unconfigured", "detail": "MEM0_API_KEY is not configured"}
        if self._last_error:
            return {"status": "degraded", "detail": self._last_error}
        return {"status": "up"}


_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    global _service
    if _service is None:
        _service = MemoryService()
    return _service


def format_memory_context(memories: list[str]) -> str:
    if not memories:
        return ""
    return "\n".join(f"- {memory}" for memory in memories)
