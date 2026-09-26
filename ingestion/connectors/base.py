"""Base classes and interfaces for AuRAG Enterprise Data Connectors."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SyncResult:
    connector_id: str
    source_type: str
    records_synced: int
    new_cursor: str | None = None
    success: bool = True
    error_message: str | None = None
    records: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BaseConnector(ABC):
    """Abstract base connector defining standard enterprise lifecycle and sync contracts."""

    def __init__(self, connector_id: str, site_id: str = "plant-mumbai-01"):
        self.connector_id = connector_id
        self.site_id = site_id

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Returns the source system identifier (e.g. 'SAP_PM', 'OSISOFT_PI', 'SHAREPOINT', 'QMS')."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verify network connectivity and credential validity against the remote system."""
        pass

    @abstractmethod
    def sync(self, cursor: str | None = None, limit: int = 100) -> SyncResult:
        """Execute an incremental synchronization run using the supplied delta cursor."""
        pass
