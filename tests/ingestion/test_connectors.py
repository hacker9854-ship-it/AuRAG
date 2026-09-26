"""Automated tests for industrial data connectors (SAP PM, OSIsoft PI, SharePoint, QMS)."""
from ingestion.connectors.osisoft_pi import OSIsoftPIConnector
from ingestion.connectors.qms import QMSConnector
from ingestion.connectors.sap_pm import SAPPMConnector
from ingestion.connectors.sharepoint import SharePointConnector


def test_sap_pm_connector_sync_and_tag_normalization():
    connector = SAPPMConnector(connector_id="sap_pm_unit_test", site_id="plant-mumbai-01")
    assert connector.health_check() is True
    assert connector.source_type == "SAP_PM"

    result = connector.sync(limit=10)
    assert result.success is True
    assert result.records_synced > 0

    equipment_records = [r for r in result.records if r["entity_type"] == "Equipment"]
    assert len(equipment_records) >= 2
    # Verify raw tag "P101" was normalized to "P-101"
    p101_rec = next(r for r in equipment_records if r["sap_id"] == "EQ-1001")
    assert p101_rec["canonical_tag"] == "P-101"

    wo_records = [r for r in result.records if r["entity_type"] == "WorkOrder"]
    assert len(wo_records) >= 1
    assert wo_records[0]["canonical_tag"] == "P-101"


def test_osisoft_pi_connector_telemetry_aggregates():
    connector = OSIsoftPIConnector(connector_id="pi_unit_test", site_id="plant-mumbai-01")
    assert connector.health_check() is True
    assert connector.source_type == "OSISOFT_PI"

    result = connector.sync()
    assert result.success is True
    assert result.records_synced >= 3

    # Check vibration and temp metrics
    vib_point = next(r for r in result.records if r["metric"] == "vibration_de")
    assert vib_point["canonical_tag"] == "P-101"
    assert vib_point["alarm_state"] == "WARNING"
    assert vib_point["max"] > vib_point["mean"]


def test_sharepoint_connector_delta_and_supersession():
    connector = SharePointConnector(connector_id="sp_unit_test", site_id="plant-mumbai-01")
    assert connector.health_check() is True
    assert connector.source_type == "SHAREPOINT"

    result = connector.sync()
    assert result.success is True
    assert result.records_synced >= 2

    # Check that document records extracted equipment tags
    doc_1 = next(r for r in result.records if "P101" in r["filename"])
    assert "P-101" in doc_1["linked_equipment_tags"]
    assert "M-101" in doc_1["linked_equipment_tags"]
    assert doc_1["revision"] == 2


def test_qms_connector_compliance_standards():
    connector = QMSConnector(connector_id="qms_unit_test", site_id="plant-mumbai-01")
    assert connector.health_check() is True
    assert connector.source_type == "QMS"

    result = connector.sync()
    assert result.success is True
    assert result.records_synced >= 3

    oisd_clause = next(r for r in result.records if "OISD-116" in r["standard"])
    assert oisd_clause["mandatory"] is True
    assert "P" in oisd_clause["target_equipment_classes"]
