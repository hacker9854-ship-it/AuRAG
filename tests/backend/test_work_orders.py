import hashlib

from backend.app.services.work_orders import (
    InvalidWorkOrderTransition,
    WorkOrderConflict,
    create_draft_work_order,
    decide_work_order,
    update_work_order,
)


class _Result:
    def __init__(self, record=None):
        self.record = record

    def single(self):
        return self.record


class _Session:
    def __init__(self, records=None):
        self.records = list(records or [])
        self.calls = []

    def run(self, query, **params):
        self.calls.append((query, params))
        record = self.records.pop(0) if self.records else None
        return _Result(record)


def test_create_draft_persists_equipment_and_predictive_event_links():
    session = _Session(
        [
            {"work_order_id": "WO-AI-1"},
            {
                "work_order": {"id": "WO-AI-1", "status": "Draft", "version": 1},
                "equipment": "P-101",
                "predictive_event_id": "PE-1",
                "decisions": [],
            },
        ]
    )

    result = create_draft_work_order(
        session,
        work_order_id="WO-AI-1",
        equipment_tag="P-101",
        event_id="PE-1",
        description="Bearing pattern match",
        recommended_action="Lubricate and inspect bearing.",
        actor="aurag",
        created_at="2026-07-20T12:00:00+00:00",
    )

    query, params = session.calls[0]
    assert "MERGE (w:WorkOrder" in query
    assert "PERFORMED_ON" in query
    assert "TRIGGERED_BY" in query
    assert params["status"] == "Draft"
    assert params["version"] == 1
    assert result["id"] == "WO-AI-1"
    assert result["equipment"] == "P-101"
    assert result["predictive_event_id"] == "PE-1"


def test_event_backed_draft_uses_stable_work_order_id():
    expected_id = (
        "WO-AI-" + hashlib.sha256(b"PE-1").hexdigest()[:10].upper()
    )
    session = _Session(
        [
            {"work_order_id": expected_id},
            {
                "work_order": {
                    "id": expected_id,
                    "status": "Draft",
                    "version": 1,
                },
                "equipment": "P-101",
                "predictive_event_id": "PE-1",
                "decisions": [],
            },
        ]
    )

    result = create_draft_work_order(
        session,
        equipment_tag="P-101",
        event_id="PE-1",
        description="Bearing pattern match",
        recommended_action="Inspect bearing.",
        actor="operator-1",
    )

    assert result["id"] == expected_id
    assert session.calls[0][1]["work_order_id"] == expected_id


def test_update_work_order_returns_canonical_relationship_context():
    session = _Session(
        [
            {"work_order_id": "WO-AI-1"},
            {
                "work_order": {"id": "WO-AI-1", "status": "In Review", "version": 2},
                "equipment": "P-101",
                "predictive_event_id": "PE-1",
                "decisions": [
                    {
                        "id": "WOD-1",
                        "decision": "edit",
                        "created_at": "2026-07-20T12:01:00+00:00",
                    }
                ],
            },
        ]
    )

    result = update_work_order(
        session,
        "WO-AI-1",
        expected_version=1,
        description="Edited description",
        recommended_action="Edited action",
        actor="operator-1",
        updated_at="2026-07-20T12:01:00+00:00",
    )

    assert result["equipment"] == "P-101"
    assert result["predictive_event_id"] == "PE-1"
    assert result["decisions"][0]["decision"] == "edit"


def test_update_work_order_uses_optimistic_version_and_raises_conflict():
    session = _Session([None])

    try:
        update_work_order(
            session,
            "WO-AI-1",
            expected_version=2,
            description="Edited description",
            recommended_action="Edited action",
            actor="operator-1",
        )
    except WorkOrderConflict as exc:
        assert exc.work_order_id == "WO-AI-1"
    else:
        raise AssertionError("stale version must raise WorkOrderConflict")

    assert "w.version = $expected_version" in session.calls[0][0]


def test_accept_and_reject_are_audited_and_transition_checked():
    approved = _Session(
        [
            {"status": "Draft", "version": 1},
            {"work_order_id": "WO-AI-1"},
            {
                "work_order": {"id": "WO-AI-1", "status": "Approved", "version": 2},
                "equipment": "P-101",
                "predictive_event_id": "PE-1",
                "decisions": [
                    {
                        "id": "WOD-1",
                        "decision": "accept",
                        "created_at": "2026-07-20T12:05:00+00:00",
                    }
                ],
            },
        ]
    )

    result = decide_work_order(
        approved,
        "WO-AI-1",
        decision="accept",
        actor="operator-1",
        expected_version=1,
        reason=None,
        decided_at="2026-07-20T12:05:00+00:00",
    )

    assert result["status"] == "Approved"
    assert "WorkOrderDecision" in approved.calls[1][0]
    assert approved.calls[1][1]["decision"] == "accept"
    assert result["equipment"] == "P-101"
    assert result["decisions"][0]["decision"] == "accept"

    invalid = _Session([{"status": "Closed", "version": 3}])
    try:
        decide_work_order(
            invalid,
            "WO-AI-2",
            decision="reject",
            actor="operator-1",
            expected_version=3,
            reason="Not applicable",
        )
    except InvalidWorkOrderTransition:
        pass
    else:
        raise AssertionError("closed work order must not be rejected")


def test_reject_requires_reason():
    try:
        decide_work_order(
            _Session(),
            "WO-AI-1",
            decision="reject",
            actor="operator-1",
            expected_version=1,
            reason=" ",
        )
    except ValueError as exc:
        assert "reason" in str(exc)
    else:
        raise AssertionError("reject must require a reason")


def test_work_order_api_maps_version_conflict(monkeypatch):
    from fastapi import HTTPException

    from backend.app.api import work_orders

    monkeypatch.setattr(
        work_orders,
        "update_work_order",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(WorkOrderConflict("WO-AI-1")),
    )

    try:
        work_orders.edit_work_order(
            "WO-AI-1",
            work_orders.WorkOrderEditRequest(
                expected_version=1,
                description="Edit",
                recommended_action="Action",
                actor="operator-1",
            ),
            session=object(),
        )
    except HTTPException as exc:
        assert exc.status_code == 409
        assert exc.detail["error"] == "work_order_conflict"
    else:
        raise AssertionError("version conflict must map to HTTP 409")


def test_work_order_api_requires_rejection_reason():
    from fastapi import HTTPException

    from backend.app.api import work_orders

    try:
        work_orders.decide(
            "WO-AI-1",
            work_orders.WorkOrderDecisionRequest(
                decision="reject",
                actor="operator-1",
                expected_version=1,
                reason="",
            ),
            session=object(),
        )
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail["error"] == "invalid_work_order_decision"
    else:
        raise AssertionError("blank rejection reason must map to HTTP 422")
