"""Base abstractions for Industrial Telemetry Adapters (Phase 2A).

Provides a unified interface for synthetic generators, public condition-monitoring
dataset replay adapters, and live telemetry sources with full provenance tracking.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional


from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    PUBLIC_DATASET = "PUBLIC_DATASET"
    SYNTHETIC_GENERATOR = "SYNTHETIC_GENERATOR"
    LIVE_SCADA = "LIVE_SCADA"
    OPCUA_TESTBED = "OPCUA_TESTBED"


class ProvenanceMetadata(BaseModel):
    data_source_type: str = "PUBLIC_DATASET"
    dataset_name: str
    dataset_record_id: Optional[str] = None
    source_reference: str
    replay_mode: bool = True
    license: Optional[str] = "NASA Open Data / Public Domain"


class TelemetryEventSchema(BaseModel):
    equipment_id: str
    sensor_id: str
    timestamp: Optional[str] = None
    vibration_mm_s: float
    bearing_temp_c: Optional[float] = None
    frequency_peak_hz: Optional[float] = None
    original_feature_val: Optional[Any] = None
    original_feature_name: Optional[str] = None
    unit: str = "mm/s"
    iso_zone: Optional[str] = None
    is_anomaly: bool = False
    threshold_exceeded: bool = False
    stage: Optional[str] = None
    provenance: ProvenanceMetadata
    data_source_type: Optional[DataSourceType] = None
    replay_mode: bool = False
    raw_feature: Optional[str] = None


class TelemetryAdapter(ABC):
    """Abstract base class for all telemetry input sources."""

    @abstractmethod
    def get_source_type(self) -> DataSourceType:
        """Return the fundamental data source classification."""
        pass

    @abstractmethod
    def get_provenance_metadata(self) -> Dict[str, Any]:
        """Return provenance metadata describing dataset, license, and replay mode."""
        pass

    @abstractmethod
    def read_event(self, record_id: Optional[str] = None) -> Dict[str, Any]:
        """Read a single normalized telemetry event."""
        pass

    @abstractmethod
    def stream_events(self) -> List[Dict[str, Any]]:
        """Return sequence of time-series events in chronological order."""
        pass

    @abstractmethod
    def normalize_reading(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw incoming payload into standard AuRAG telemetry schema."""
        pass
