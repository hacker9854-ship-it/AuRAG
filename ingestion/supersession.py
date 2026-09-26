"""Document Version Supersession and Revision Tracking.

Ensures operators retrieve only current, active revisions of Standard Operating
Procedures (SOPs) and safety guidelines. When Rev 3 of a procedure is uploaded,
prior revisions (Rev 1, Rev 2) are flagged as SUPERSEDED and filtered out of
standard GraphRAG retrieval while preserved for historical compliance audits.
"""
import re
from dataclasses import dataclass
from typing import NamedTuple

# Regex matching document revision tags in filenames or titles
# Examples: "SOP-101-Rev2.pdf", "HAZOP_P101_v3.pdf", "PROC-042_r1.pdf", "SOP-01 (Rev. 4)"
_REV_PATTERN = re.compile(
    r"^(.*?)[-_.\s]+(?:rev|revision|v|ver|r)[-_.\s]*0*(\d+)(?:\.([a-zA-Z0-9]+))?$",
    re.IGNORECASE,
)


class DocRevision(NamedTuple):
    base_id: str
    revision: int
    extension: str
    original_name: str


def parse_document_revision(filename: str) -> DocRevision | None:
    """Extract the base document identifier and integer revision number from a filename."""
    if not filename:
        return None

    match = _REV_PATTERN.match(filename.strip())
    if match:
        base, rev_str, ext = match.groups()
        base_clean = base.strip("-_ ")
        return DocRevision(
            base_id=base_clean,
            revision=int(rev_str),
            extension=ext or "",
            original_name=filename,
        )

    # Return revision 1 if no explicit revision is parsed
    clean_name = filename.rsplit(".", 1)[0]
    ext = filename.rsplit(".", 1)[1] if "." in filename else ""
    return DocRevision(
        base_id=clean_name,
        revision=1,
        extension=ext,
        original_name=filename,
    )


class SupersessionManager:
    """Manages active vs superseded document states across ingestion runs."""

    def __init__(self):
        # Maps base_id -> latest DocRevision
        self._latest_revisions: dict[str, DocRevision] = {}

    def register_document(self, filename: str) -> dict:
        """Evaluate a document against known revisions and determine supersession status."""
        doc_rev = parse_document_revision(filename)
        if not doc_rev:
            return {"status": "ACTIVE", "revision": 1, "supersedes": None}

        base_id = doc_rev.base_id.upper()
        current_latest = self._latest_revisions.get(base_id)

        if current_latest is None or doc_rev.revision > current_latest.revision:
            self._latest_revisions[base_id] = doc_rev
            superseded_file = current_latest.original_name if current_latest else None
            return {
                "status": "ACTIVE",
                "base_id": doc_rev.base_id,
                "revision": doc_rev.revision,
                "supersedes": superseded_file,
            }
        elif doc_rev.revision < current_latest.revision:
            return {
                "status": "SUPERSEDED",
                "base_id": doc_rev.base_id,
                "revision": doc_rev.revision,
                "superseded_by": current_latest.original_name,
            }
        else:
            # Same revision
            return {
                "status": "ACTIVE",
                "base_id": doc_rev.base_id,
                "revision": doc_rev.revision,
                "supersedes": None,
            }
