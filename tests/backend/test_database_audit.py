"""Automated tests for relational database models, audit logging, and connector APIs."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from backend.app.db.database import Base, get_db, init_db
from backend.app.db.models import AuditEvent, ConnectorSync, QuarantineItem
from backend.app.services.audit import log_audit_event, query_audit_events
from backend.app.main import app

# Ephemeral in-memory SQLite database using StaticPool to share state across sessions
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def setup_test_db():
    init_db(TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)



@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_log_and_query_audit_event(db_session):
    event = log_audit_event(
        db=db_session,
        user_id="operator-rahul",
        site_id="plant-mumbai-01",
        role="ReliabilityEngineer",
        action_type="RCA_INSPECTION",
        resource_type="EQUIPMENT",
        resource_id="P-101",
        details={"query": "Why did bearing fail?", "confidence": 0.95},
    )

    assert event.event_id is not None
    assert event.user_id == "operator-rahul"
    assert event.action_type == "RCA_INSPECTION"

    # Query events by site
    results = query_audit_events(db_session, site_id="plant-mumbai-01")
    assert len(results) == 1
    assert results[0]["user_id"] == "operator-rahul"
    assert results[0]["details"]["confidence"] == 0.95

    # Cross-site query isolation
    cross_site = query_audit_events(db_session, site_id="plant-jamnagar-02")
    assert len(cross_site) == 0


def test_connectors_api_list_and_sync(monkeypatch):
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        # 1. List Connectors
        res_list = client.get("/api/connectors")
        assert res_list.status_code == 200
        data = res_list.json()
        assert "connectors" in data
        connector_ids = [c["connector_id"] for c in data["connectors"]]
        assert "sap_pm" in connector_ids
        assert "osisoft_pi" in connector_ids

        # 2. Trigger Sync on SAP PM
        res_sync = client.post("/api/connectors/sap_pm/sync")
        assert res_sync.status_code == 200
        sync_data = res_sync.json()
        assert sync_data["connector_id"] == "sap_pm"
        assert sync_data["status"] == "COMPLETED"
        assert sync_data["records_synced"] > 0

        # 3. Query Audit Events via API
        res_audit = client.get("/api/audit/events")
        assert res_audit.status_code == 200
        audit_data = res_audit.json()
        assert audit_data["total_returned"] >= 1
        assert any(e["action_type"] == "CONNECTOR_SYNC" for e in audit_data["events"])
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_quarantine_review_flow(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        # Seed quarantine item
        item = QuarantineItem(
            item_id="QRN-TEST-01",
            source_system="SHAREPOINT",
            filename="corrupt_drawing.pdf",
            sha256="abc123sha256fake",
            quarantine_reason="Corrupt magic bytes",
            severity="HIGH",
        )
        db_session.add(item)
        db_session.commit()

        # List quarantine items
        res_list = client.get("/api/connectors/quarantine")
        assert res_list.status_code == 200
        items = res_list.json()["quarantine_items"]
        assert len(items) == 1
        assert items[0]["filename"] == "corrupt_drawing.pdf"

        # Review quarantine item (APPROVE)
        res_rev = client.post(
            "/api/connectors/quarantine/QRN-TEST-01/review",
            json={"decision": "APPROVED", "notes": "Verified safe by chief engineer."},
        )
        assert res_rev.status_code == 200
        assert res_rev.json()["status"] == "APPROVED"
    finally:
        app.dependency_overrides.pop(get_db, None)
