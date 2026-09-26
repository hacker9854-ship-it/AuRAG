"""RQ jobs for materializing and ingesting immutable document objects."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import truststore

truststore.inject_into_ssl()

from ingestion import pipeline
from ingestion.workers.storage import ObjectRef, get_object_store, verify_file


def process_object(reference: dict) -> dict:
    ref = ObjectRef.from_dict(reference)
    store = get_object_store(ref.backend)
    work_root = Path(
        os.environ.get(
            "INGEST_WORK_DIR",
            str(pipeline.REPO_ROOT / ".runtime" / "ingest-work"),
        )
    ).resolve()
    job_root = work_root / ref.sha256
    local_path = job_root / ref.filename
    try:
        store.download(ref, local_path)
        verify_file(local_path, ref.sha256)
        return pipeline.ingest_file(local_path)
    finally:
        shutil.rmtree(job_root, ignore_errors=True)


def process_file(path: str) -> dict:
    """Backward-compatible local job entry point."""
    source = Path(path)
    store = get_object_store()
    return process_object(store.put_file(source).to_dict())
