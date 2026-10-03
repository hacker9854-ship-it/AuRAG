"""Automated test suite for Phase 2A public dataset replay adapter and synthetic generators.

Verifies:
- Schema normalization to the canonical AuRAG telemetry format
- Provenance metadata preservation (dataset_name, dataset_record_id, source_reference)
- Historical timestamp preservation
- Invalid record and malformed schema rejection
- Differentiation of PUBLIC_DATASET vs SYNTHETIC_GENERATOR vs OPCUA_TESTBED
"""
import os
import pytest
from datetime import datetime

from telemetry.adapters.base import DataSourceType, TelemetryEventSchema
from telemetry.adapters.public_dataset import PublicDatasetReplayAdapter
from telemetry.adapters.synthetic import SyntheticTelemetryAdapter
from telemetry.adapters.opcua import OPCUATelemetryAdapter


def test_public_dataset_adapter_loads_default_fixture():
    adapter = PublicDatasetReplayAdapter(equipment_id="REPLAY-ASSET-01")
    records = adapter.list_records()
    assert len(records) >= 5, "Expected at least 5 sample records from NASA IMS dataset"
    assert "NASA-IMS-T2-REC-042" in records


def test_public_dataset_schema_normalization():
    adapter = PublicDatasetReplayAdapter(equipment_id="REPLAY-ASSET-01")
    event = adapter.read_event("NASA-IMS-T2-REC-042")

    # Validate against TelemetryEventSchema
    schema = TelemetryEventSchema(**event)
    assert schema.equipment_id == "REPLAY-ASSET-01"
    assert schema.sensor_id == "REPLAY-SENSOR-BEARING-01"
    assert schema.data_source_type == DataSourceType.PUBLIC_DATASET
    assert schema.replay_mode is True
    assert schema.unit == "mm/s"
    assert schema.vibration_mm_s == 5.42
    assert schema.threshold_exceeded is True
    assert "NASA IMS Bearing Run-to-Failure" in schema.provenance.dataset_name
    assert schema.provenance.dataset_record_id == "NASA-IMS-T2-REC-042"
    assert "nasa.gov" in schema.provenance.source_reference


def test_public_dataset_timestamp_preservation():
    adapter = PublicDatasetReplayAdapter(equipment_id="REPLAY-ASSET-01")
    event = adapter.read_event("NASA-IMS-T2-REC-001")

    # Timestamp must match the historical NASA IMS run timestamp (2004-02-12)
    assert "2004-02-12T10:32:39" in event["timestamp"]
    assert event["provenance"]["dataset_record_id"] == "NASA-IMS-T2-REC-001"
    assert event["threshold_exceeded"] is False


def test_public_dataset_iteration():
    adapter = PublicDatasetReplayAdapter(equipment_id="REPLAY-ASSET-01")
    stream = adapter.stream_events()
    events = list(stream)
    assert len(events) == 5

    # Check progression: first nominal (1.85 mm/s), later excursion (5.42 mm/s), last spall (11.75 mm/s)
    assert events[0]["vibration_mm_s"] == 1.85
    assert events[3]["vibration_mm_s"] == 5.42
    assert events[4]["vibration_mm_s"] == 11.75


def test_public_dataset_invalid_record_rejection():
    adapter = PublicDatasetReplayAdapter(equipment_id="REPLAY-ASSET-01")
    with pytest.raises(KeyError, match="Record ID 'NON_EXISTENT_REC' not found"):
        adapter.read_event("NON_EXISTENT_REC")


def test_public_dataset_invalid_fixture_content_rejection(tmp_path):
    # Malformed record missing mandatory raw vibration
    bad_file = tmp_path / "bad_fixture.json"
    bad_file.write_text('{"metadata": {}, "records": [{"record_id": "REC-BAD"}]}', encoding="utf-8")

    adapter = PublicDatasetReplayAdapter(fixture_path=str(bad_file))
    with pytest.raises(ValueError, match="Malformed record"):
        adapter.read_event("REC-BAD")


def test_synthetic_telemetry_adapter():
    synth_adapter = SyntheticTelemetryAdapter(equipment_id="P-101A")
    event = synth_adapter.generate_reading(vib_value=5.4)

    assert event["equipment_id"] == "P-101A"
    assert event["sensor_id"] == "VIB-301-BEARING"
    assert event["data_source_type"] == DataSourceType.SYNTHETIC_GENERATOR
    assert event["replay_mode"] is False
    assert event["vibration_mm_s"] == 5.4
    assert event["threshold_exceeded"] is True
    assert "Synthetic" in event["provenance"]["dataset_name"]


def test_opcua_telemetry_adapter_testbed():
    opc_adapter = OPCUATelemetryAdapter(equipment_id="OPCUA-NODE-01")
    event = opc_adapter.read_tag("ns=2;s=P101.Vibration")

    assert event["equipment_id"] == "OPCUA-NODE-01"
    assert event["data_source_type"] == DataSourceType.OPCUA_TESTBED
    assert event["replay_mode"] is True
    assert event["raw_feature"] == "ns=2;s=P101.Vibration"
    assert "testbed" in event["provenance"]["dataset_name"].lower()
