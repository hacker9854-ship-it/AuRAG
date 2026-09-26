from backend.app.services.knowledge_risk import (
    build_person_risk,
    list_knowledge_risks,
)


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def data(self):
        return self._rows


class _Session:
    def __init__(self, rows):
        self.rows = rows
        self.params = None

    def run(self, _query, **params):
        self.params = params
        return _Result(self.rows)


def test_person_risk_prioritizes_imminent_retirement_and_uncovered_assets():
    risk = build_person_risk(
        {
            "person_id": "PER-001",
            "name": "Vikram Singh",
            "role": "Maintenance Supervisor",
            "department": "Mechanical",
            "years_to_retirement": 1,
            "work_orders": ["WO-1003", "WO-1009"],
            "equipment": ["C-201", "T-501"],
            "critical_equipment": ["C-201"],
            "failure_events": ["FE-002", "FE-005"],
            "documents": ["DOC-MAINT"],
            "uncovered_equipment": ["C-201"],
        }
    )

    assert risk["risk_score"] == 88
    assert risk["severity"] == "critical"
    assert risk["knowledge_coverage"] == {
        "covered_assets": 1,
        "uncovered_assets": 1,
        "coverage_pct": 50.0,
    }
    assert risk["recommended_actions"][0]["type"] == "capture_knowledge"


def test_person_risk_handles_no_linked_operational_knowledge():
    risk = build_person_risk(
        {
            "person_id": "PER-099",
            "name": "New Engineer",
            "role": "Engineer",
            "department": "Process",
            "years_to_retirement": 20,
            "work_orders": [],
            "equipment": [],
            "critical_equipment": [],
            "failure_events": [],
            "documents": [],
            "uncovered_equipment": [],
        }
    )

    assert risk["risk_score"] == 0
    assert risk["severity"] == "monitored"
    assert risk["knowledge_coverage"]["coverage_pct"] == 100.0


def test_list_knowledge_risks_filters_and_sorts_results():
    session = _Session(
        [
            {
                "person_id": "PER-006",
                "name": "Priya Nair",
                "role": "Junior Engineer",
                "department": "Mechanical",
                "years_to_retirement": 30,
                "work_orders": ["WO-1002"],
                "equipment": ["P-101"],
                "critical_equipment": [],
                "failure_events": ["FE-001"],
                "documents": [],
                "uncovered_equipment": [],
            },
            {
                "person_id": "PER-001",
                "name": "Vikram Singh",
                "role": "Supervisor",
                "department": "Mechanical",
                "years_to_retirement": 1,
                "work_orders": ["WO-1003"],
                "equipment": ["C-201"],
                "critical_equipment": ["C-201"],
                "failure_events": ["FE-002"],
                "documents": ["DOC-1"],
                "uncovered_equipment": ["C-201"],
            },
        ]
    )

    result = list_knowledge_risks(session, retirement_horizon=5)

    assert [person["person_id"] for person in result["people"]] == ["PER-001"]
    assert result["summary"] == {
        "people_at_risk": 1,
        "critical": 1,
        "elevated": 0,
        "uncovered_assets": 1,
    }
    assert session.params == {"horizon": 5}


def test_knowledge_risk_api_rejects_invalid_horizon():
    from fastapi import HTTPException

    from backend.app.api.knowledge_risk import knowledge_risks

    try:
        knowledge_risks(retirement_horizon=0, session=object())
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail["error"] == "invalid_retirement_horizon"
    else:
        raise AssertionError("zero-year horizon must be rejected")


def test_knowledge_risk_person_api_returns_404(monkeypatch):
    from fastapi import HTTPException

    from backend.app.api import knowledge_risk

    monkeypatch.setattr(knowledge_risk, "get_person_knowledge_risk", lambda *_args, **_kwargs: None)

    try:
        knowledge_risk.person_knowledge_risk("PER-404", session=object())
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail["error"] == "person_not_found"
    else:
        raise AssertionError("unknown person must return 404")
