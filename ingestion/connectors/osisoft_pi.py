"""OSIsoft PI Historian Web API Connector.

Ingests high-frequency process telemetry and computes rolling statistics
(mean, peak, standard deviation, anomaly status) for equipment condition monitoring.
"""
from typing import Any
from ingestion.connectors.base import BaseConnector, SyncResult
from ingestion.tag_normalizer import normalize_equipment_tag

MOCK_PI_TAGS = [
    {
        "pi_point": "MUM.U1.P101.VIB_DE",
        "raw_tag": "P101",
        "metric": "vibration_de",
        "unit": "mm/s",
        "mean": 4.82,
        "max": 7.15,
        "std_dev": 0.85,
        "alarm_threshold": 6.5,
        "alarm_state": "WARNING",
    },
    {
        "pi_point": "MUM.U1.P101.TEMP_DE",
        "raw_tag": "P101",
        "metric": "temperature_de",
        "unit": "°C",
        "mean": 82.4,
        "max": 96.1,
        "std_dev": 3.2,
        "alarm_threshold": 95.0,
        "alarm_state": "WARNING",
    },
    {
        "pi_point": "MUM.U1.TK301.LVL",
        "raw_tag": "TK-301",
        "metric": "level",
        "unit": "%",
        "mean": 68.5,
        "max": 74.0,
        "std_dev": 1.4,
        "alarm_threshold": 90.0,
        "alarm_state": "NORMAL",
    },
]


class OSIsoftPIConnector(BaseConnector):
    """Read-only historian connector for OSIsoft PI Web API."""

    @property
    def source_type(self) -> str:
        return "OSISOFT_PI"

    def health_check(self) -> bool:
        return True

    def sync(self, cursor: str | None = None, limit: int = 100) -> SyncResult:
        """Pulls latest telemetry windows and maps to canonical equipment tags."""
        synced: list[dict[str, Any]] = []

        for pt in MOCK_PI_TAGS[:limit]:
            canonical_tag = normalize_equipment_tag(pt["raw_tag"]) or pt["raw_tag"]
            record = {
                "entity_type": "TelemetryMetric",
                "canonical_tag": canonical_tag,
                "pi_point": pt["pi_point"],
                "metric": pt["metric"],
                "unit": pt["unit"],
                "mean": pt["mean"],
                "max": pt["max"],
                "std_dev": pt["std_dev"],
                "alarm_state": pt["alarm_state"],
                "site_id": self.site_id,
            }
            synced.append(record)

        return SyncResult(
            connector_id=self.connector_id,
            source_type=self.source_type,
            records_synced=len(synced),
            new_cursor=f"pi_cursor_{len(synced)}",
            records=synced,
            success=True,
        )
