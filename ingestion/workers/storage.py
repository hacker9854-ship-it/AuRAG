"""Shared object storage for asynchronous ingestion jobs."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from ingestion.pipeline import REPO_ROOT

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def safe_filename(filename: str) -> str:
    name = Path(filename).name
    cleaned = _SAFE_NAME.sub("-", name).strip(".-")
    if not cleaned:
        raise ValueError("filename must contain at least one safe character")
    return cleaned[:180]


@dataclass(frozen=True)
class ObjectRef:
    backend: str
    key: str
    sha256: str
    filename: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict) -> "ObjectRef":
        return cls(
            backend=str(value["backend"]),
            key=str(value["key"]),
            sha256=str(value["sha256"]),
            filename=safe_filename(str(value["filename"])),
        )


class LocalObjectStore:
    backend = "local"

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, content: bytes, filename: str) -> ObjectRef:
        digest = sha256_bytes(content)
        name = safe_filename(filename)
        key = f"{digest[:2]}/{digest}/{name}"
        target = self._path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(content)
        return ObjectRef(self.backend, key, digest, name)

    def put_file(self, path: Path) -> ObjectRef:
        return self.put_bytes(path.read_bytes(), path.name)

    def download(self, ref: ObjectRef, destination: Path) -> None:
        source = self._path(ref.key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    def _path(self, key: str) -> Path:
        target = (self.root / key).resolve()
        if self.root not in target.parents:
            raise ValueError("object key escaped the configured storage root")
        return target


class S3ObjectStore:
    backend = "s3"

    def __init__(self):
        import boto3

        self.bucket = os.environ.get("INGEST_S3_BUCKET", "")
        if not self.bucket:
            raise RuntimeError("INGEST_S3_BUCKET is required for s3 ingestion storage")
        self.prefix = os.environ.get("INGEST_S3_PREFIX", "aurag-ingest").strip("/")
        self.client = boto3.client(
            "s3",
            endpoint_url=os.environ.get("INGEST_S3_ENDPOINT") or None,
            region_name=os.environ.get("INGEST_S3_REGION") or None,
            aws_access_key_id=os.environ.get("INGEST_S3_ACCESS_KEY_ID") or None,
            aws_secret_access_key=os.environ.get("INGEST_S3_SECRET_ACCESS_KEY") or None,
        )

    def put_bytes(self, content: bytes, filename: str) -> ObjectRef:
        digest = sha256_bytes(content)
        name = safe_filename(filename)
        key = "/".join(part for part in (self.prefix, digest, name) if part)
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            Metadata={"sha256": digest, "original-filename": name},
        )
        return ObjectRef(self.backend, key, digest, name)

    def put_file(self, path: Path) -> ObjectRef:
        return self.put_bytes(path.read_bytes(), path.name)

    def download(self, ref: ObjectRef, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(self.bucket, ref.key, str(destination))


def get_object_store(backend: str | None = None):
    selected = (backend or os.environ.get("INGEST_STORAGE_BACKEND", "local")).lower()
    if selected == "s3":
        return S3ObjectStore()
    if selected == "local":
        root = Path(
            os.environ.get(
                "INGEST_OBJECT_DIR",
                str(REPO_ROOT / ".runtime" / "ingest-objects"),
            )
        )
        return LocalObjectStore(root)
    raise RuntimeError(f"Unsupported INGEST_STORAGE_BACKEND: {selected}")


def verify_file(path: Path, expected_sha256: str) -> None:
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ValueError(
            f"Ingestion object checksum mismatch: expected {expected_sha256}, got {actual}"
        )
