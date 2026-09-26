import json

from backend.app.services.evaluations import (
    count_evaluations,
    create_evaluation,
    deserialize_evaluation,
    summarize_evaluations,
    summarize_evaluations_db,
    update_evaluation,
)


class _Result:
    def __init__(self, record=None, rows=None):
        self._record = record
        self._rows = rows or []

    def single(self):
        return self._record

    def data(self):
        return self._rows


class _Session:
    def __init__(self, record=None, results=None):
        self.record = record
        self.results = list(results or [])
        self.calls = []

    def run(self, query, **params):
        self.calls.append((query, params))
        if self.results:
            return self.results.pop(0)
        return _Result(self.record)


def test_create_evaluation_persists_full_answer_metadata_as_json():
    session = _Session()

    created = create_evaluation(
        session,
        score_id="score-1",
        query="Why did P-101 fail?",
        answer="Bearing wear followed missed lubrication.",
        routed_agent="rca",
        citations=["FE-001", "WO-1002"],
        graph_paths=[{"type": "FailureEvent", "id": "FE-001"}],
        retrieved_context=[("FE-001", "failure evidence")],
        created_at="2026-07-20T10:00:00+00:00",
    )

    assert created["score_id"] == "score-1"
    assert created["ragas_status"] == "scoring"
    params = session.calls[0][1]
    assert json.loads(params["citations_json"]) == ["FE-001", "WO-1002"]
    assert '"FailureEvent"' in params["graph_paths_json"]
    assert '"failure evidence"' in params["retrieved_context_json"]


def test_update_and_deserialize_evaluation_scores():
    session = _Session(
        {
            "evaluation": {
                "score_id": "score-1",
                "query": "Q",
                "answer": "A",
                "routed_agent": "copilot",
                "citations_json": '["C-1"]',
                "graph_paths_json": "[]",
                "retrieved_context_json": '[["C-1", "context"]]',
                "ragas_status": "scored",
                "faithfulness": 0.8,
                "context_precision": 0.7,
                "answer_relevancy": 0.9,
                "low_faithfulness": False,
                "created_at": "2026-07-20T10:00:00+00:00",
                "completed_at": "2026-07-20T10:00:03+00:00",
                "scoring_duration_ms": 3000,
                "detail": None,
            }
        }
    )

    update_evaluation(
        session,
        "score-1",
        status="scored",
        scores={"faithfulness": 0.8, "context_precision": 0.7, "answer_relevancy": 0.9},
        low_faithfulness=False,
        duration_ms=3000,
        completed_at="2026-07-20T10:00:03+00:00",
    )
    result = deserialize_evaluation(session.record["evaluation"])

    assert "MATCH (e:EvaluationRun" in session.calls[0][0]
    assert session.calls[0][1]["faithfulness"] == 0.8
    assert result["ragas_scores"] == {
        "faithfulness": 0.8,
        "context_precision": 0.7,
        "answer_relevancy": 0.9,
    }
    assert result["retrieved_context"] == [["C-1", "context"]]


def test_summary_aggregates_statuses_metrics_and_low_faithfulness():
    summary = summarize_evaluations(
        [
            {
                "ragas_status": "scored",
                "routed_agent": "rca",
                "ragas_scores": {
                    "faithfulness": 0.8,
                    "context_precision": 0.6,
                    "answer_relevancy": 0.9,
                },
                "low_faithfulness": False,
            },
            {
                "ragas_status": "scored",
                "routed_agent": "copilot",
                "ragas_scores": {
                    "faithfulness": 0.4,
                    "context_precision": 0.8,
                    "answer_relevancy": 0.7,
                },
                "low_faithfulness": True,
            },
            {
                "ragas_status": "error",
                "routed_agent": "copilot",
                "ragas_scores": {},
                "low_faithfulness": False,
            },
        ]
    )

    assert summary["total"] == 3
    assert summary["status_counts"] == {"scored": 2, "error": 1}
    assert summary["agent_counts"] == {"rca": 1, "copilot": 2}
    assert summary["low_faithfulness_count"] == 1
    assert summary["averages"] == {
        "faithfulness": 0.6,
        "context_precision": 0.7,
        "answer_relevancy": 0.8,
    }


def test_database_summary_aggregates_complete_history():
    session = _Session(
        results=[
            _Result(
                {
                    "total": 350,
                    "low_count": 12,
                    "faithfulness": 0.81234,
                    "context_precision": 0.72345,
                    "answer_relevancy": 0.93456,
                }
            ),
            _Result(rows=[{"key": "scored", "count": 340}, {"key": "error", "count": 10}]),
            _Result(rows=[{"key": "rca", "count": 200}, {"key": "copilot", "count": 150}]),
            _Result(
                rows=[
                    {
                        "day": "2026-07-20",
                        "total": 4,
                        "faithfulness": 0.75,
                        "context_precision": 0.8,
                        "answer_relevancy": 0.9,
                        "low_count": 1,
                    },
                    {
                        "day": "2026-07-19",
                        "total": 3,
                        "faithfulness": 0.7,
                        "context_precision": 0.76,
                        "answer_relevancy": 0.84,
                        "low_count": 0,
                    },
                ]
            ),
        ]
    )

    summary = summarize_evaluations_db(session)

    assert summary["total"] == 350
    assert summary["status_counts"] == {"scored": 340, "error": 10}
    assert summary["low_faithfulness_count"] == 12
    assert summary["averages"]["faithfulness"] == 0.812
    assert [point["day"] for point in summary["trend"]] == ["2026-07-19", "2026-07-20"]
    assert summary["trend"][1]["low_faithfulness_count"] == 1


def test_count_evaluations_forwards_all_filters():
    session = _Session(record={"total": 7})

    total = count_evaluations(
        session,
        status="scored",
        agent="rca",
        low_faithfulness=True,
    )

    assert total == 7
    assert session.calls[0][1] == {
        "status": "scored",
        "agent": "rca",
        "low_faithfulness": True,
    }


def test_score_job_can_be_reloaded_from_durable_store_after_cache_miss(monkeypatch):
    from backend.app.core import ragas_jobs

    session = _Session()
    score_id = ragas_jobs.create_score_job(
        session,
        query="Q",
        agent_response="A",
        routed_agent="copilot",
        citations=["C-1"],
        graph_paths=[],
        retrieved_context=[("C-1", "context")],
    )

    ragas_jobs._JOBS.clear()
    monkeypatch.setattr(
        ragas_jobs,
        "get_evaluation",
        lambda _session, _score_id: {
            "score_id": _score_id,
            "ragas_status": "scoring",
            "ragas_scores": {},
            "low_faithfulness": False,
            "detail": None,
        },
    )

    assert ragas_jobs.get_score_job(score_id, session=session)["score_id"] == score_id


def test_evaluations_api_returns_history_and_summary(monkeypatch):
    from backend.app.api import evaluations

    records = [
        {
            "score_id": "score-1",
            "ragas_status": "scored",
            "routed_agent": "rca",
            "ragas_scores": {
                "faithfulness": 0.8,
                "context_precision": 0.7,
                "answer_relevancy": 0.9,
            },
            "low_faithfulness": False,
        }
    ]
    monkeypatch.setattr(evaluations, "list_evaluations", lambda *_args, **_kwargs: records)
    monkeypatch.setattr(evaluations, "count_evaluations", lambda *_args, **_kwargs: 51)
    monkeypatch.setattr(
        evaluations,
        "summarize_evaluations_db",
        lambda _session: summarize_evaluations(records),
    )

    result = evaluations.evaluation_results(session=object())
    assert result["items"] == records
    assert result["total"] == 51
    assert result["has_more"] is True
    summary = evaluations.evaluation_summary(session=object())
    assert summary["total"] == 1
    assert summary["averages"]["faithfulness"] == 0.8


def test_evaluation_detail_returns_404(monkeypatch):
    from fastapi import HTTPException

    from backend.app.api import evaluations

    monkeypatch.setattr(evaluations, "get_evaluation", lambda *_args, **_kwargs: None)

    try:
        evaluations.evaluation_detail("missing", session=object())
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail["error"] == "evaluation_not_found"
    else:
        raise AssertionError("missing evaluation must return 404")
