"""Public Industrial Dataset Replay Adapter (Phase 2A).

Consumes authentic, published run-to-failure condition-monitoring data
(NASA IMS Bearing Dataset) and normalizes it into AuRAG's telemetry schema
with rigorous provenance tracking and honest UI labeling.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from telemetry.adapters.base import DataSourceType, TelemetryAdapter

logger = logging.getLogger(__name__)

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "nasa_ims_bearing_sample.json"


class PublicDatasetReplayAdapter(TelemetryAdapter):
    """Replay adapter for empirical industrial condition-monitoring datasets."""

    def __init__(
        self,
        fixture_path: Optional[Any] = None,
        equipment_id: str = "REPLAY-ASSET-01",
    ):
        self.fixture_path = Path(fixture_path) if fixture_path is not None else FIXTURE_PATH
        self.equipment_id = equipment_id
        self._data = self._load_fixture()

    def _load_fixture(self) -> Dict[str, Any]:
        """Load and parse the verified representative dataset fixture."""
        if not self.fixture_path.exists():
            raise FileNotFoundError(f"Public dataset fixture not found at {self.fixture_path}")
        with open(self.fixture_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_source_type(self) -> DataSourceType:
        return DataSourceType.PUBLIC_DATASET

    def get_dataset_metadata(self) -> Dict[str, Any]:
        return self._data.get("dataset_metadata", {})

    def get_provenance_metadata(self, record_id: str = "NASA-IMS-T2-REC-042") -> Dict[str, Any]:
        meta = self.get_dataset_metadata()
        return {
            "data_source_type": DataSourceType.PUBLIC_DATASET.value,
            "dataset_name": meta.get("dataset_name", "NASA IMS Bearing Run-to-Failure Dataset"),
            "dataset_record_id": record_id,
            "source_reference": meta.get(
                "source_url",
                "https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/",
            ),
            "replay_mode": True,
            "equipment_id": self.equipment_id,
            "disclosure": meta.get(
                "provenance_disclosure",
                "Public industrial condition-monitoring data replay (preprocessed representative progression fixture)",
            ),
        }

    def list_records(self) -> List[str]:
        """Return all available record IDs in the fixture."""
        return [r.get("record_id") for r in self._data.get("records", []) if r.get("record_id")]

    def normalize_reading(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw NASA record into standard AuRAG telemetry format."""
        if "vibration_mm_s" not in raw_record and "vibration_rms_g" not in raw_record:
            raise ValueError("Malformed record: missing vibration features")

        record_id = raw_record.get("record_id", "UNKNOWN-REC")
        vibration_mm_s = float(raw_record.get("vibration_mm_s", 0.0))
        bearing_temp_c = float(raw_record.get("bearing_temp_c", 0.0))
        freq_peak = float(raw_record.get("frequency_peak_hz", 0.0))

        return {
            "equipment_id": self.equipment_id,
            "sensor_id": "REPLAY-SENSOR-BEARING-01",
            "timestamp": raw_record.get("timestamp"),
            "vibration_mm_s": vibration_mm_s,
            "bearing_temp_c": bearing_temp_c,
            "frequency_peak_hz": freq_peak,
            "original_feature_val": raw_record.get("vibration_rms_g"),
            "original_feature_name": "vibration_rms_g",
            "unit": "mm/s",
            "iso_zone": raw_record.get("iso_zone"),
            "is_anomaly": vibration_mm_s > 4.5,
            "threshold_exceeded": vibration_mm_s > 4.5,
            "stage": raw_record.get("stage"),
            "data_source_type": DataSourceType.PUBLIC_DATASET,
            "replay_mode": True,
            "provenance": self.get_provenance_metadata(record_id=record_id),
        }

    def read_event(self, record_id: Optional[str] = None) -> Dict[str, Any]:
        """Read a specific record by ID, or the canonical Zone C excursion record."""
        target_id = record_id or "NASA-IMS-T2-REC-042"
        records = self._data.get("records", [])
        for r in records:
            if r.get("record_id") == target_id:
                return self.normalize_reading(r)

        raise KeyError(f"Record ID '{target_id}' not found in public dataset fixture")

    def stream_events(self) -> List[Dict[str, Any]]:
        """Return all time-series records in chronological progression."""
        records = self._data.get("records", [])
        return [self.normalize_reading(r) for r in records]
