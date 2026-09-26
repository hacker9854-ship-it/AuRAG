import asyncio


class _Request:
    def __init__(self, content: bytes):
        self.content = content

    async def body(self):
        return self.content


class _Job:
    id = "ingest-abc"


def test_document_upload_stores_and_queues_object_reference(monkeypatch, tmp_path):
    from backend.app.api import ingestion
    from ingestion.workers.storage import LocalObjectStore

    calls = {}

    class Queue:
        def __init__(self, name, connection):
            calls["queue_name"] = name
            calls["connection"] = connection

        def enqueue(self, function, reference, **kwargs):
            calls["function"] = function
            calls["reference"] = reference
            calls["kwargs"] = kwargs
            return _Job()

    monkeypatch.setattr(
        ingestion,
        "get_object_store",
        lambda: LocalObjectStore(tmp_path / "objects"),
    )
    monkeypatch.setattr(ingestion, "Queue", Queue)
    monkeypatch.setattr(ingestion.Redis, "from_url", lambda url: f"redis:{url}")

    result = asyncio.run(
        ingestion.enqueue_document(_Request(b"maintenance record"), "record.txt")
    )

    assert result["status"] == "queued"
    assert result["job_id"] == "ingest-abc"
    assert calls["queue_name"] == "aurag-ingest"
    assert calls["reference"]["filename"] == "record.txt"
    assert calls["kwargs"]["job_id"].startswith("ingest-")


def test_document_upload_rejects_empty_body():
    from fastapi import HTTPException

    from backend.app.api import ingestion

    try:
        asyncio.run(ingestion.enqueue_document(_Request(b""), "empty.txt"))
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail["error"] == "empty_document"
    else:
        raise AssertionError("empty document must be rejected")
