from pathlib import Path

import pytest

from ingestion.workers.storage import LocalObjectStore, ObjectRef
from ingestion.workers.tasks import process_object
from ingestion.workers.watcher import IngestHandler


class _Job:
    id = "job-1"


class _Queue:
    def __init__(self):
        self.calls = []

    def enqueue(self, function, reference, **kwargs):
        self.calls.append((function, reference, kwargs))
        return _Job()


def test_watcher_queues_an_immutable_object_reference(tmp_path):
    source = tmp_path / "watch" / "report.txt"
    source.parent.mkdir()
    source.write_text("P-101 bearing observation", encoding="utf-8")
    queue = _Queue()
    store = LocalObjectStore(tmp_path / "objects")

    handler = IngestHandler(queue, store=store)
    handler._maybe_enqueue(str(source))

    function, reference, kwargs = queue.calls[0]
    assert function is process_object
    assert reference["backend"] == "local"
    assert reference["filename"] == "report.txt"
    assert kwargs["job_id"] == f"ingest-{reference['sha256']}"
    assert (tmp_path / "objects" / reference["key"]).read_text(encoding="utf-8").startswith("P-101")


def test_worker_materializes_from_shared_store_and_cleans_work_dir(
    tmp_path,
    monkeypatch,
):
    producer_store = LocalObjectStore(tmp_path / "shared-objects")
    reference = producer_store.put_bytes(b"document", "incident.txt")
    work_root = tmp_path / "consumer-work"
    seen = {}

    monkeypatch.setenv("INGEST_OBJECT_DIR", str(tmp_path / "shared-objects"))
    monkeypatch.setenv("INGEST_WORK_DIR", str(work_root))
    monkeypatch.setattr(
        "ingestion.workers.tasks.pipeline.ingest_file",
        lambda path: seen.update(path=Path(path), body=Path(path).read_bytes())
        or {"status": "new"},
    )

    result = process_object(reference.to_dict())

    assert result == {"status": "new"}
    assert seen["body"] == b"document"
    assert not (work_root / reference.sha256).exists()


def test_worker_rejects_checksum_mismatch(tmp_path, monkeypatch):
    store = LocalObjectStore(tmp_path / "objects")
    reference = store.put_bytes(b"trusted", "report.txt")
    source = tmp_path / "objects" / reference.key
    source.write_bytes(b"tampered")

    monkeypatch.setenv("INGEST_OBJECT_DIR", str(tmp_path / "objects"))
    monkeypatch.setenv("INGEST_WORK_DIR", str(tmp_path / "work"))
    monkeypatch.setattr(
        "ingestion.workers.tasks.pipeline.ingest_file",
        lambda _path: pytest.fail("tampered files must not be ingested"),
    )

    with pytest.raises(ValueError, match="checksum mismatch"):
        process_object(ObjectRef.from_dict(reference.to_dict()).to_dict())
