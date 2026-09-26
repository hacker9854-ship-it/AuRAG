from datetime import datetime, timedelta, timezone

from telemetry.worker import TelemetryWorker


def test_worker_publishes_warning_without_user_interaction():
    created = []
    published = []

    worker = TelemetryWorker(
        equipment_tags=["P-101"],
        scan_fn=lambda _session, tag, drift: {
            "equipment": tag,
            "reading": {"vibration_mm_s": 7.5},
            "warning": {
                "matched_failure_event": "FE-001",
                "similarity": 0.95,
                "symptom": "Bearing vibration",
            },
        },
        create_fn=lambda _session, **kwargs: created.append(kwargs)
        or {"id": "PE-1", "_created": True},
        publish_fn=published.append,
        now=lambda: datetime(2026, 7, 20, 12, tzinfo=timezone.utc),
        drift_schedule=[1.0],
    )

    result = worker.run_cycle(session=object())

    assert result["events_created"] == 1
    assert created[0]["equipment_tag"] == "P-101"
    assert created[0]["failure_event_id"] == "FE-001"
    assert published == ["PE-1"]


def test_worker_deduplicates_same_failure_during_cooldown():
    current = datetime(2026, 7, 20, 12, tzinfo=timezone.utc)
    created = []

    worker = TelemetryWorker(
        equipment_tags=["P-101"],
        scan_fn=lambda *_args: {
            "equipment": "P-101",
            "reading": {},
            "warning": {
                "matched_failure_event": "FE-001",
                "similarity": 0.95,
                "symptom": "Bearing vibration",
            },
        },
        create_fn=lambda _session, **kwargs: created.append(kwargs)
        or {"id": "PE-1", "_created": len(created) == 1},
        publish_fn=lambda _event_id: None,
        now=lambda: current,
        cooldown=timedelta(minutes=30),
        drift_schedule=[1.0],
    )

    first = worker.run_cycle(session=object())
    second = worker.run_cycle(session=object())

    assert first["events_created"] == 1
    assert second["events_created"] == 0
    assert second["deduplicated"] == 1
    assert len(created) == 2
