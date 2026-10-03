"""Synthetic Telemetry Adapter (Phase 2A).

Wraps AuRAG's mathematical signature-drift generator for deterministic demonstration
and local CI testing with explicit SYNTHETIC_GENERATOR provenance labeling.
"""
import uuid
from typing import Any, Dict, List, Optional

from telemetry.adapters.base import DataSourceType, TelemetryAdapter
from telemetry.generator import NOMINAL, generate_reading


class SyntheticTelemetryAdapter(TelemetryAdapter):
    """Adapter for mathematically simulated sensor drift."""

    def __init__(self, equipment_id: Optional[str] = None, equipment_tag: Optional[str] = None):
        self.equipment_tag = equipment_id or equipment_tag or "P-101A"

    def get_source_type(self) -> DataSourceType:
        return DataSourceType.SYNTHETIC_GENERATOR

    def get_provenance_metadata(self) -> Dict[str, Any]:
        return {
            "data_source_type": DataSourceType.SYNTHETIC_GENERATOR.value,
            "dataset_name": "AuRAG Synthetic Industrial Generator",
            "dataset_record_id": f"SYNTH-{self.equipment_tag}-{uuid.uuid4().hex[:6].upper()}",
            "source_reference": "telemetry/generator.py",
            "replay_mode": False,
            "equipment_id": self.equipment_tag,
            "disclosure": "SYNTHETIC DEMO: Simulated sensor drift based on Neo4j failure signatures",
        }

    def normalize_reading(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure standard fields and units are present."""
        equipment = raw_data.get("equipment", self.equipment_tag)
        vibration = float(raw_data.get("vibration_mm_s", NOMINAL["vibration_mm_s"]))
        bearing_temp = float(raw_data.get("bearing_temp_c", NOMINAL["bearing_temp_c"]))

        return {
            "equipment_id": equipment,
            "sensor_id": "VIB-301-BEARING",
            "vibration_mm_s": vibration,
            "bearing_temp_c": bearing_temp,
            "unit": "mm/s",
            "is_anomaly": vibration > 4.5,
            "threshold_exceeded": vibration > 4.5,
            "data_source_type": DataSourceType.SYNTHETIC_GENERATOR,
            "replay_mode": False,
            "provenance": self.get_provenance_metadata(),
        }

    def generate_reading(self, vib_value: float = 5.4, temp_value: float = 88.0) -> Dict[str, Any]:
        """Direct generator for synthetic sensor reading."""
        raw = {
            "equipment": self.equipment_tag,
            "vibration_mm_s": vib_value,
            "bearing_temp_c": temp_value,
        }
        return self.normalize_reading(raw)

    def read_event(
        self,
        record_id: Optional[str] = None,
        session=None,
        drift_pct: float = 0.0,
        drift_toward: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a single reading."""
        if session is not None:
            raw = generate_reading(
                session=session,
                equipment_tag=self.equipment_tag,
                drift_toward=drift_toward,
                drift_pct=drift_pct,
            )
        else:
            # Offline standalone reading
            val = NOMINAL["vibration_mm_s"] + (7.5 - NOMINAL["vibration_mm_s"]) * drift_pct
            temp = NOMINAL["bearing_temp_c"] + (88.0 - NOMINAL["bearing_temp_c"]) * drift_pct
            raw = {
                "equipment": self.equipment_tag,
                "vibration_mm_s": val,
                "bearing_temp_c": temp,
            }
        return self.normalize_reading(raw)

    def stream_events(self) -> List[Dict[str, Any]]:
        """Stream a 5-step drift progression from healthy to failure."""
        events = []
        for step in [0.0, 0.25, 0.5, 0.75, 1.0]:
            events.append(self.read_event(drift_pct=step))
        return events
