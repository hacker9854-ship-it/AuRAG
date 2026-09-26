def test_scan_persists_and_publishes_warning_event(monkeypatch):
    from backend.app.api import telemetry

    monkeypatch.setattr(
        telemetry,
        "generate_reading",
        lambda *_args, **_kwargs: {"equipment": "P-101", "vibration_mm_s": 7.5},
    )
    monkeypatch.setattr(
        telemetry,
        "match_reading",
        lambda *_args, **_kwargs: [
            {
                "failure_event_id": "FE-001",
                "similarity": 0.95,
                "symptom": "Bearing vibration",
                "root_cause": "Missed lubrication",
            }
        ],
    )
    monkeypatch.setattr(
        telemetry,
        "build_warning",
        lambda *_args, **_kwargs: {
            "equipment": "P-101",
            "matched_failure_event": "FE-001",
            "similarity": 0.95,
            "symptom": "Bearing vibration",
        },
    )
    monkeypatch.setattr(telemetry, "meta_for", lambda *_args: {})
    monkeypatch.setattr(
        telemetry,
        "create_predictive_event",
        lambda *_args, **_kwargs: {
            "id": "PE-1",
            "status": "unread",
            "_created": True,
        },
    )
    published = []
    monkeypatch.setattr(telemetry, "publish_event", published.append)

    result = telemetry.scan(
        telemetry.ScanRequest(equipment_tag="P-101", drift_toward="FE-001", drift_pct=1),
        session=object(),
    )

    assert result["predictive_event"]["id"] == "PE-1"
    assert result["warning"]["event_id"] == "PE-1"
    assert published == ["PE-1"]


def test_repeated_scan_does_not_republish_deduplicated_event(monkeypatch):
    from backend.app.api import telemetry

    monkeypatch.setattr(
        telemetry,
        "generate_reading",
        lambda *_args, **_kwargs: {"equipment": "P-101", "vibration_mm_s": 7.5},
    )
    monkeypatch.setattr(telemetry, "match_reading", lambda *_args, **_kwargs: [{}])
    monkeypatch.setattr(
        telemetry,
        "build_warning",
        lambda *_args, **_kwargs: {
            "equipment": "P-101",
            "matched_failure_event": "FE-001",
            "similarity": 0.95,
            "symptom": "Bearing vibration",
        },
    )
    monkeypatch.setattr(telemetry, "meta_for", lambda *_args: {})
    monkeypatch.setattr(
        telemetry,
        "create_predictive_event",
        lambda *_args, **_kwargs: {
            "id": "PE-STABLE",
            "status": "unread",
            "_created": False,
        },
    )
    published = []
    monkeypatch.setattr(telemetry, "publish_event", published.append)

    result = telemetry.scan(
        telemetry.ScanRequest(equipment_tag="P-101", drift_toward="FE-001", drift_pct=1),
        session=object(),
    )

    assert result["warning"]["event_id"] == "PE-STABLE"
    assert published == []


def test_telemetry_draft_creates_persistent_work_order(monkeypatch):
    from backend.app.api import telemetry

    monkeypatch.setattr(
        telemetry,
        "draft_work_order",
        lambda *_args, **_kwargs: {
            "description": "Draft description",
            "recommended_action": "Inspect bearing",
        },
    )
    monkeypatch.setattr(
        telemetry,
        "create_draft_work_order",
        lambda *_args, **kwargs: {
            "id": "WO-AI-1",
            "status": "Draft",
            "version": 1,
            **kwargs,
        },
    )

    result = telemetry.draft(
        telemetry.DraftRequest(
            equipment_tag="P-101",
            event_id="PE-1",
            actor="operator-1",
            top_match={
                "failure_event_id": "FE-001",
                "similarity": 0.95,
                "symptom": "Bearing vibration",
                "root_cause": "Missed lubrication",
            },
        ),
        session=object(),
    )

    assert result["id"] == "WO-AI-1"
    assert result["event_id"] == "PE-1"
    assert result["actor"] == "operator-1"
