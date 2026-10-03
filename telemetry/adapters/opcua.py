"""Optional OPC-UA Testbed Telemetry Adapter (Phase 2A Task 2A.9).

Provides a simulated industrial OPC-UA node telemetry ingestion bridge
with explicit OPCUA_TESTBED disclosure.
"""
from typing import Any, Dict, List, Optional
from telemetry.adapters.base import DataSourceType, TelemetryAdapter


class OPCUATestbedAdapter(TelemetryAdapter):
    """Low-risk simulated OPC-UA testbed adapter."""

    def __init__(
        self,
        endpoint_url: str = "opc.tcp://localhost:4840/freeopcua/server/",
        equipment_id: str = "OPCUA-PUMP-01",
    ):
        self.endpoint_url = endpoint_url
        self.equipment_id = equipment_id

    def get_source_type(self) -> DataSourceType:
        return DataSourceType.OPCUA_TESTBED

    def get_provenance_metadata(self) -> Dict[str, Any]:
        return {
            "data_source_type": DataSourceType.OPCUA_TESTBED.value,
            "dataset_name": "AuRAG OPC-UA Emulated Testbed",
            "dataset_record_id": f"OPCUA-NODE-{self.equipment_id}",
            "source_reference": self.endpoint_url,
            "replay_mode": True,
            "equipment_id": self.equipment_id,
            "disclosure": "OPC-UA TESTBED / REPLAY: Emulated industrial OPC-UA node stream",
        }

    def normalize_reading(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        vib = float(raw_data.get("vibration_mm_s", 2.2))
        temp = float(raw_data.get("bearing_temp_c", 58.0))
        tag = raw_data.get("tag_name", "ns=2;s=Vibration_RMS")
        return {
            "equipment_id": self.equipment_id,
            "sensor_id": tag,
            "raw_feature": tag,
            "vibration_mm_s": vib,
            "bearing_temp_c": temp,
            "unit": "mm/s",
            "is_anomaly": vib > 4.5,
            "threshold_exceeded": vib > 4.5,
            "data_source_type": DataSourceType.OPCUA_TESTBED,
            "replay_mode": True,
            "provenance": self.get_provenance_metadata(),
        }

    def read_tag(self, tag_name: str, vibration: float = 5.45, temp: float = 86.0) -> Dict[str, Any]:
        return self.normalize_reading({
            "tag_name": tag_name,
            "vibration_mm_s": vibration,
            "bearing_temp_c": temp,
        })

    def read_event(self, record_id: Optional[str] = None) -> Dict[str, Any]:
        return self.normalize_reading({"vibration_mm_s": 5.45, "bearing_temp_c": 86.0})

    def stream_events(self) -> List[Dict[str, Any]]:
        return [
            self.normalize_reading({"vibration_mm_s": 2.1, "bearing_temp_c": 54.0}),
            self.normalize_reading({"vibration_mm_s": 5.45, "bearing_temp_c": 86.0}),
        ]


# Alias for flexible importing
OPCUATelemetryAdapter = OPCUATestbedAdapter
