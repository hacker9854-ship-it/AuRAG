"""Entry point: python -m ingestion.cli ingest <path> [<path> ...]"""
import sys
from pathlib import Path

from ingestion.pipeline import ingest_file


def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] != "ingest":
        print("Usage: python -m ingestion.cli ingest <path> [<path> ...]", file=sys.stderr)
        sys.exit(1)

    for raw_path in sys.argv[2:]:
        ingest_file(Path(raw_path))


if __name__ == "__main__":
    main()
