"""Quarantine and File Integrity Scanner.

Isolates malformed, malicious, or duplicate documents before they enter the
ingestion pipeline or pollute the Neo4j Knowledge Graph.
"""
import hashlib
import os
from pathlib import Path
from typing import NamedTuple

DISALLOWED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".vbs", ".ps1", ".dll", ".so", ".bin", ".js", ".py"
}

ALLOWED_EXTENSIONS = {
    ".pdf", ".txt", ".md", ".csv", ".json", ".docx", ".xlsx", ".png", ".jpg", ".jpeg", ".tiff"
}


class ScanResult(NamedTuple):
    is_safe: bool
    quarantine_reason: str | None
    severity: str
    sha256: str


def scan_file_bytes(content: bytes, filename: str) -> ScanResult:
    """Evaluate file content and metadata for corruption, security risks, or invalid formats."""
    digest = hashlib.sha256(content).hexdigest()
    ext = Path(filename).suffix.lower()

    # 1. Zero-byte or empty file check
    if len(content) == 0:
        return ScanResult(
            is_safe=False,
            quarantine_reason="Empty file (0 bytes)",
            severity="LOW",
            sha256=digest,
        )

    # 2. Dangerous executable extension check
    if ext in DISALLOWED_EXTENSIONS:
        return ScanResult(
            is_safe=False,
            quarantine_reason=f"Disallowed executable extension '{ext}'",
            severity="CRITICAL",
            sha256=digest,
        )

    # 3. Unrecognized extension check
    if ext not in ALLOWED_EXTENSIONS:
        return ScanResult(
            is_safe=False,
            quarantine_reason=f"Unrecognized file extension '{ext}'",
            severity="MEDIUM",
            sha256=digest,
        )

    # 4. PDF header validation (magic bytes check)
    if ext == ".pdf" and not content.startswith(b"%PDF-"):
        return ScanResult(
            is_safe=False,
            quarantine_reason="Corrupt PDF: missing %PDF- magic bytes header",
            severity="HIGH",
            sha256=digest,
        )

    return ScanResult(
        is_safe=True,
        quarantine_reason=None,
        severity="NONE",
        sha256=digest,
    )
