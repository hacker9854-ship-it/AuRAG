from pathlib import Path

from ingestion import pipeline


class _Driver:
    def __init__(self, session):
        self._session = session

    def session(self, **_kwargs):
        return self._session


class _Session:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def run(self, query, **params):
        self.calls.append((query, params))
        return type(
            "Result",
            (),
            {
                "single": lambda self: None,
                "__iter__": lambda self: iter(()),
            },
        )()


def test_ingestion_sets_hash_only_after_vector_index_succeeds(monkeypatch, tmp_path):
    source = tmp_path / "retry.md"
    source.write_text("P-101 evidence", encoding="utf-8")
    session = _Session()
    order = []

    monkeypatch.setattr(pipeline, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(pipeline, "get_driver", lambda: _Driver(session))
    monkeypatch.setattr(pipeline, "get_database", lambda: "neo4j")
    monkeypatch.setattr(pipeline, "get_gemini_client", object)
    monkeypatch.setattr(
        pipeline,
        "resolve_document",
        lambda *_args: ("DOC-RETRY", "changed"),
    )
    monkeypatch.setattr(pipeline, "route_file", lambda _path: "clean_text")
    monkeypatch.setattr(
        pipeline,
        "build_raw_chunks",
        lambda *_args, **_kwargs: [pipeline.RawChunk("1", "P-101 evidence", [])],
    )
    monkeypatch.setattr(pipeline, "clear_existing_chunks", lambda *_args: order.append("clear"))
    monkeypatch.setattr(pipeline, "clear_existing_connections", lambda *_args: None)
    monkeypatch.setattr(pipeline, "load_known_entities", lambda *_args: ({"P-101"}, set()))
    monkeypatch.setattr(pipeline, "load_chunk", lambda *_args, **_kwargs: order.append("load"))
    monkeypatch.setattr(
        pipeline,
        "set_document_hash",
        lambda *_args, **_kwargs: order.append("hash"),
    )

    monkeypatch.setattr(
        pipeline,
        "index_document_chunks",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("qdrant down")),
    )

    try:
        pipeline.ingest_file(source)
    except RuntimeError as exc:
        assert "qdrant down" in str(exc)
    else:
        raise AssertionError("indexing failure must propagate")

    assert order == ["clear", "load"]


def test_changed_document_is_not_cleared_before_parsing_succeeds(monkeypatch, tmp_path):
    source = tmp_path / "retry.md"
    source.write_text("P-101 evidence", encoding="utf-8")
    session = _Session()
    cleared = []

    monkeypatch.setattr(pipeline, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(pipeline, "get_driver", lambda: _Driver(session))
    monkeypatch.setattr(pipeline, "get_database", lambda: "neo4j")
    monkeypatch.setattr(pipeline, "get_gemini_client", object)
    monkeypatch.setattr(
        pipeline,
        "resolve_document",
        lambda *_args: ("DOC-RETRY", "changed"),
    )
    monkeypatch.setattr(pipeline, "route_file", lambda _path: "clean_text")
    monkeypatch.setattr(
        pipeline,
        "build_raw_chunks",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("gemini down")),
    )
    monkeypatch.setattr(
        pipeline,
        "clear_existing_chunks",
        lambda *_args: cleared.append("chunks"),
    )
    monkeypatch.setattr(
        pipeline,
        "clear_existing_connections",
        lambda *_args: cleared.append("connections"),
    )

    try:
        pipeline.ingest_file(source)
    except RuntimeError as exc:
        assert "gemini down" in str(exc)
    else:
        raise AssertionError("parse failure must propagate")

    assert cleared == []
