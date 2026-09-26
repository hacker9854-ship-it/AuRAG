"""Quality Management System (QMS) and Regulatory Compliance Connector.

Synchronizes statutory regulatory clauses (Factories Act, OISD, PESO, ISO 45001),
internal audit findings, and Non-Conformance Reports (NCRs).
"""
from typing import Any
from ingestion.connectors.base import BaseConnector, SyncResult
from ingestion.tag_normalizer import extract_canonical_tags

MOCK_QMS_CLAUSES = [
    {
        "clause_id": "OISD-116-CL-4.2",
        "standard": "OISD-116",
        "title": "Fire Protection Facilities for Petroleum Refineries",
        "description": "All hydrocarbon pumps handling liquids above flash point must have secondary containment and remote ESD trip valves.",
        "target_equipment_classes": ["P"],
        "mandatory": True,
    },
    {
        "clause_id": "FACT-1948-SEC-28",
        "standard": "Factories Act 1948",
        "title": "Hoists, Lifts, and Pressure Vessels Inspection",
        "description": "Pressure vessels and storage tanks exceeding 500 liters capacity must be inspected by a competent person once every 12 months.",
        "target_equipment_classes": ["TK", "HEX", "V"],
        "mandatory": True,
    },
    {
        "clause_id": "ISO-45001-8.1.2",
        "standard": "ISO 45001:2018",
        "title": "Eliminating Hazards and Reducing OH&S Risks",
        "description": "Documented hierarchy of controls must be verified prior to hot work on hydrocarbon-bearing equipment.",
        "target_equipment_classes": ["P", "TK", "C"],
        "mandatory": True,
    },
]


class QMSConnector(BaseConnector):
    """Connector for Quality Management & Regulatory Compliance records."""

    @property
    def source_type(self) -> str:
        return "QMS"

    def health_check(self) -> bool:
        return True

    def sync(self, cursor: str | None = None, limit: int = 100) -> SyncResult:
        synced: list[dict[str, Any]] = []

        for item in MOCK_QMS_CLAUSES[:limit]:
            record = {
                "entity_type": "ComplianceStandard",
                "clause_id": item["clause_id"],
                "standard": item["standard"],
                "title": item["title"],
                "description": item["description"],
                "target_equipment_classes": item["target_equipment_classes"],
                "mandatory": item["mandatory"],
                "site_id": self.site_id,
            }
            synced.append(record)

        return SyncResult(
            connector_id=self.connector_id,
            source_type=self.source_type,
            records_synced=len(synced),
            new_cursor=f"qms_cursor_{len(synced)}",
            records=synced,
            success=True,
        )
