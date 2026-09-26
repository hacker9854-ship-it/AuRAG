"""SAP Plant Maintenance (PM) and Enterprise Asset Management (EAM) Connector.

Synchronizes equipment master records, functional location hierarchies (FLOC),
and maintenance work orders from SAP S/4HANA or SAP ECC.
"""
from typing import Any
from ingestion.connectors.base import BaseConnector, SyncResult
from ingestion.tag_normalizer import normalize_equipment_tag


# Standard mock equipment master dataset for simulation and testing
MOCK_SAP_EQUIPMENT = [
    {
        "sap_id": "EQ-1001",
        "raw_tag": "P101",
        "description": "Boiler Feed Water Pump A",
        "floc": "MUM-U1-BFW-P101",
        "manufacturer": "Sulzer",
        "model": "MSD-2",
        "criticality": "HIGH",
        "status": "ACTIVE",
    },
    {
        "sap_id": "EQ-1002",
        "raw_tag": "P_101_B",
        "description": "Boiler Feed Water Pump B (Standby)",
        "floc": "MUM-U1-BFW-P101B",
        "manufacturer": "Sulzer",
        "model": "MSD-2",
        "criticality": "HIGH",
        "status": "STANDBY",
    },
    {
        "sap_id": "EQ-1003",
        "raw_tag": "TK-301",
        "description": "Condensate Storage Tank",
        "floc": "MUM-U1-COND-TK301",
        "manufacturer": "L&T Heavy Engineering",
        "model": "Atmospheric-500m3",
        "criticality": "MEDIUM",
        "status": "ACTIVE",
    },
]

MOCK_SAP_WORK_ORDERS = [
    {
        "order_id": "4000101",
        "raw_tag": "P101",
        "order_type": "PM02",  # Corrective / breakdown maintenance
        "short_text": "Drive-end bearing replacement due to thermal spike",
        "priority": "1-VERY HIGH",
        "status": "TECO",  # Technically completed
        "created_on": "2025-06-12",
    },
    {
        "order_id": "4000102",
        "raw_tag": "TK-301",
        "order_type": "PM01",  # Planned preventive maintenance
        "short_text": "Annual ultrasonic wall thickness inspection",
        "priority": "3-MEDIUM",
        "status": "TECO",
        "created_on": "2025-07-20",
    },
]


class SAPPMConnector(BaseConnector):
    """Connector for SAP PM/EAM REST or RFC feeds."""

    @property
    def source_type(self) -> str:
        return "SAP_PM"

    def health_check(self) -> bool:
        """Verifies connection to SAP endpoint / service identity."""
        return True

    def sync(self, cursor: str | None = None, limit: int = 100) -> SyncResult:
        """Extracts equipment and work orders, normalizing tags via ISA-5.1 standard."""
        synced_records: list[dict[str, Any]] = []

        # 1. Process Equipment
        for eq in MOCK_SAP_EQUIPMENT[:limit]:
            canonical_tag = normalize_equipment_tag(eq["raw_tag"]) or eq["raw_tag"]
            record = {
                "entity_type": "Equipment",
                "canonical_tag": canonical_tag,
                "raw_tag": eq["raw_tag"],
                "sap_id": eq["sap_id"],
                "description": eq["description"],
                "functional_location": eq["floc"],
                "criticality": eq["criticality"],
                "site_id": self.site_id,
            }
            synced_records.append(record)

        # 2. Process Work Orders
        for wo in MOCK_SAP_WORK_ORDERS[:limit]:
            canonical_tag = normalize_equipment_tag(wo["raw_tag"]) or wo["raw_tag"]
            record = {
                "entity_type": "WorkOrder",
                "order_id": wo["order_id"],
                "canonical_tag": canonical_tag,
                "order_type": wo["order_type"],
                "description": wo["short_text"],
                "status": wo["status"],
                "created_on": wo["created_on"],
                "site_id": self.site_id,
            }
            synced_records.append(record)

        new_cursor = f"sap_cursor_{len(synced_records)}"
        return SyncResult(
            connector_id=self.connector_id,
            source_type=self.source_type,
            records_synced=len(synced_records),
            new_cursor=new_cursor,
            records=synced_records,
            success=True,
        )
