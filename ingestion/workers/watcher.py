"""Watch a local folder, publish immutable objects, and enqueue object refs."""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from redis import Redis
from rq import Queue
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ingestion.workers.storage import get_object_store
from ingestion.workers.tasks import process_object

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

DEBOUNCE_SECONDS = 2.0


class IngestHandler(FileSystemEventHandler):
    def __init__(self, queue: Queue, store=None):
        self.queue = queue
        self.store = store or get_object_store()
        self._last_seen: dict[str, float] = {}

    def _maybe_enqueue(self, src_path: str) -> None:
        now = time.monotonic()
        if now - self._last_seen.get(src_path, 0) < DEBOUNCE_SECONDS:
            return
        self._last_seen[src_path] = now
        reference = self.store.put_file(Path(src_path))
        job = self.queue.enqueue(
            process_object,
            reference.to_dict(),
            job_id=f"ingest-{reference.sha256}",
        )
        print(f"enqueued {reference.filename} ({reference.sha256[:12]}) -> job {job.id}")

    def on_created(self, event):
        if not event.is_directory:
            self._maybe_enqueue(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._maybe_enqueue(event.src_path)


def main() -> None:
    redis_url = os.environ.get("REDIS_URL")
    watch_dir = REPO_ROOT / os.environ.get("INGEST_WATCH_DIR", "data/incoming")
    if not redis_url:
        print("Missing REDIS_URL in .env", file=sys.stderr)
        sys.exit(1)
    watch_dir.mkdir(parents=True, exist_ok=True)

    queue = Queue("aurag-ingest", connection=Redis.from_url(redis_url))
    observer = Observer()
    observer.schedule(IngestHandler(queue), str(watch_dir), recursive=False)
    observer.start()
    print(
        f"Watching {watch_dir} -> shared object storage -> "
        f"Redis queue 'aurag-ingest' ({redis_url})"
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
