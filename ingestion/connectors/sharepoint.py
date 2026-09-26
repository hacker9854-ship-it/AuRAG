"""Microsoft 365 SharePoint Graph API Document Connector.

Synchronizes standard operating procedures (SOPs), maintenance manuals,
and engineering guidelines with delta-cursor and version supersession support.
"""
from typing import Any
from ingestion.connectors.base import BaseConnector, SyncResult
from ingestion.supersession import SupersessionManager
from ingestion.tag_normalizer import extract_canonical_tags

MOCK_SHAREPOINT_DOCS = [
    {
        "doc_id": "SP-DOC-001",
        "filename": "SOP-P101-Startup-Rev2.pdf",
        "title": "Standard Operating Procedure: Feed Pump P-101 Startup Sequence",
        "author": "P. Sharma",
        "modified_at": "2025-05-10T08:30:00Z",
        "content_snippet": "Ensure suction valve is 100% open before energizing pump P101 motor M-101. Verify seal flush pressure.",
        "etag": 'W/"12345"',
    },
    {
        "doc_id": "SP-DOC-002",
        "filename": "HAZOP-Tank-TK301-Rev1.pdf",
        "title": "Hazard & Operability Study: Condensate Tank TK-301 Overfill Protection",
        "author": "S. Iyer",
        "modified_at": "2025-04-18T14:15:00Z",
        "content_snippet": "High level alarm on TK301 triggers interlock I-301 to isolate inlet valve CV-105.",
        "etag": 'W/"67890"',
    },
]


class SharePointConnector(BaseConnector):
    """Incremental SharePoint document library synchronizer."""

    def __init__(self, connector_id: str, site_id: str = "plant-mumbai-01"):
        super().__init__(connector_id, site_id)
        self.supersession_mgr = SupersessionManager()

    @property
    def source_type(self) -> str:
        return "SHAREPOINT"

    def health_check(self) -> bool:
        return True

    def sync(self, cursor: str | None = None, limit: int = 100) -> SyncResult:
        synced: list[dict[str, Any]] = []

        for item in MOCK_SHAREPOINT_DOCS[:limit]:
            # Evaluate supersession
            sup_info = self.supersession_mgr.register_document(item["filename"])
            # Extract mentioned equipment tags
            tags = extract_canonical_tags(item["content_snippet"])

            record = {
                "entity_type": "Document",
                "doc_id": item["doc_id"],
                "filename": item["filename"],
                "title": item["title"],
                "author": item["author"],
                "etag": item["etag"],
                "lifecycle_status": sup_info["status"],
                "revision": sup_info["revision"],
                "supersedes": sup_info.get("supersedes"),
                "linked_equipment_tags": tags,
                "site_id": self.site_id,
            }
            synced.append(record)

        return SyncResult(
            connector_id=self.connector_id,
            source_type=self.source_type,
            records_synced=len(synced),
            new_cursor=f"sp_cursor_{len(synced)}",
            records=synced,
            success=True,
        )
