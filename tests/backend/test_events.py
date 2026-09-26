from backend.app.services.events import (
    create_predictive_event,
    list_predictive_events,
    notification_payload,
    predictive_event_identity,
)
from backend.app.api.events import format_sse_event


class _Result:
    def __init__(self, record=None, rows=None):
        self.record = record
        self.rows = rows or []

    def single(self):
        return self.record

    def data(self):
        return self.rows


class _Session:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def run(self, query, **params):
        self.calls.append((query, params))
        return self.result


def test_predictive_event_is_idempotent_and_links_failure_equipment():
    session = _Session(
        _Result({"event": {"id": "PE-1", "status": "unread"}, "created": True})
    )

    event = create_predictive_event(
        session,
        event_id="PE-1",
        equipment_tag="P-101",
        failure_event_id="FE-001",
        similarity=0.93,
        symptom="Bearing vibration",
        reading={"vibration_mm_s": 7.5},
        detected_at="2026-07-20T12:00:00+00:00",
    )

    query, params = session.calls[0]
    assert "MERGE (event:PredictiveEvent" in query
    assert "dedupe_key" in query
    assert "TRIGGERS" in query
    assert params["similarity"] == 0.93
    assert event["id"] == "PE-1"
    assert event["_created"] is True


def test_predictive_event_identity_is_stable_inside_cooldown_bucket():
    first = predictive_event_identity(
        "P-101", "FE-001", "2026-07-21T08:00:00+00:00", 1800
    )
    retry = predictive_event_identity(
        "P-101", "FE-001", "2026-07-21T08:10:00+00:00", 1800
    )
    later = predictive_event_identity(
        "P-101", "FE-001", "2026-07-21T08:31:00+00:00", 1800
    )

    assert retry == first
    assert later != first


def test_notification_payload_has_stable_event_id_and_action_link():
    payload = notification_payload(
        {
            "id": "PE-1",
            "equipment": "P-101",
            "failure_event_id": "FE-001",
            "similarity": 0.93,
            "symptom": "Bearing vibration",
            "status": "unread",
            "detected_at": "2026-07-20T12:00:00+00:00",
        }
    )

    assert payload == {
        "id": "PE-1",
        "type": "predictive_warning",
        "title": "P-101 requires attention",
        "description": "Bearing vibration",
        "severity": "high",
        "equipment": "P-101",
        "failure_event_id": "FE-001",
        "similarity": 0.93,
        "status": "unread",
        "detected_at": "2026-07-20T12:00:00+00:00",
        "action_href": "/predictive-watch?event=PE-1",
    }


def test_list_predictive_events_supports_since_cursor():
    session = _Session(_Result(rows=[{"event": {"id": "PE-2", "status": "unread"}}]))

    result = list_predictive_events(session, since="PE-1", limit=20)

    assert result == [{"id": "PE-2", "status": "unread"}]
    assert session.calls[0][1] == {"since": "PE-1", "limit": 20}


def test_sse_event_contains_id_type_and_json_payload():
    wire = format_sse_event({"id": "PE-2", "equipment": "P-101"})

    assert wire.startswith("id: PE-2\nevent: predictive_warning\n")
    assert '"equipment":"P-101"' in wire
    assert wire.endswith("\n\n")
