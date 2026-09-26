from types import SimpleNamespace

from retrieval import rerank as rerank_module


def test_cohere_rerank_preserves_candidate_keys(monkeypatch):
    calls = {}

    class Client:
        def rerank(self, **kwargs):
            calls.update(kwargs)
            return SimpleNamespace(
                results=[
                    SimpleNamespace(index=1, relevance_score=0.9),
                    SimpleNamespace(index=0, relevance_score=0.4),
                ]
            )

    monkeypatch.setenv("RERANK_PROVIDER", "cohere")
    monkeypatch.setattr(rerank_module, "get_cohere_client", lambda: Client())

    result = rerank_module.rerank(
        "pump failure",
        [("A", "generic text"), ("FE-001", "bearing wear")],
        top_n=2,
    )

    assert [item[0] for item in result] == ["FE-001", "A"]
    assert calls["model"] == rerank_module.COHERE_MODEL
    assert calls["documents"] == ["generic text", "bearing wear"]


def test_local_rerank_remains_available(monkeypatch):
    class Model:
        def predict(self, pairs):
            assert pairs == [("query", "one"), ("query", "two")]
            return [0.1, 0.8]

    monkeypatch.setenv("RERANK_PROVIDER", "local")
    monkeypatch.setattr(rerank_module, "get_local_model", lambda: Model())

    result = rerank_module.rerank(
        "query",
        [("A", "one"), ("B", "two")],
        top_n=1,
    )

    assert result == [("B", "two", 0.8)]
