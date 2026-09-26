import sys
import types
from pathlib import Path

sys.modules.setdefault("google", types.ModuleType("google"))
google_genai = types.ModuleType("google.genai")
google_genai.types = types.SimpleNamespace(GenerateContentConfig=lambda **kwargs: kwargs)
sys.modules.setdefault("google.genai", google_genai)
truststore = types.ModuleType("truststore")
truststore.inject_into_ssl = lambda: None
sys.modules.setdefault("truststore", truststore)
fake_pdfplumber = types.ModuleType("pdfplumber")
fake_pdfplumber.open = lambda path: None
sys.modules.setdefault("pdfplumber", fake_pdfplumber)
fake_pytesseract = types.ModuleType("pytesseract")
fake_pytesseract.TesseractNotFoundError = type("TesseractNotFoundError", (Exception,), {})
fake_pytesseract.Output = types.SimpleNamespace(DICT="dict")
fake_pytesseract.pytesseract = types.SimpleNamespace(tesseract_cmd="")
sys.modules.setdefault("pytesseract", fake_pytesseract)
fake_pil = types.ModuleType("PIL")
fake_pil.Image = types.SimpleNamespace(open=lambda path: object())
sys.modules.setdefault("PIL", fake_pil)

from ingestion.parsers import vision_pnid
from ingestion.parsers.vision_pnid import PIDConnection, PIDEntity, PIDPage
from ingestion import pipeline


def test_vision_extract_preserves_connections_per_page(monkeypatch, tmp_path):
    class FakePage:
        def to_image(self, resolution):
            return type("Rendered", (), {"original": object()})()

    class FakePdf:
        pages = [FakePage()]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr("pdfplumber.open", lambda path: FakePdf())
    monkeypatch.setattr(
        vision_pnid,
        "_extract_page",
        lambda image, client: vision_pnid.PIDExtraction(
            entities=[PIDEntity(tag="P-101", label="pump", symbol_type="pump")],
            connections=[PIDConnection(from_tag="P-101", to_tag="V-301", line_type="process")],
            page_summary="pump to valve",
        ),
    )
    monkeypatch.setattr(vision_pnid, "_audit_connections", lambda image, client: [])

    pages = vision_pnid.extract(tmp_path / "drawing.pdf", object())

    assert isinstance(pages[0], PIDPage)
    assert pages[0].connections == [PIDConnection(from_tag="P-101", to_tag="V-301", line_type="process")]


def test_connection_audit_merges_without_duplicate_visual_edges():
    primary = [PIDConnection(from_tag="P-101", to_tag="V-301", line_type="process")]
    audit = [
        PIDConnection(from_tag="P-101", to_tag="V-301", line_type="process"),
        PIDConnection(from_tag="PT-101", to_tag="PIC-101", line_type="signal"),
    ]

    assert vision_pnid._merge_connections(primary, audit) == [
        PIDConnection(from_tag="P-101", to_tag="V-301", line_type="process"),
        PIDConnection(from_tag="PT-101", to_tag="PIC-101", line_type="signal"),
    ]


def test_load_connections_merges_directed_edges_and_reports_unmatched():
    class Result:
        def single(self):
            return None

    class Session:
        def __init__(self):
            self.calls = []

        def run(self, query, **params):
            self.calls.append((query, params))
            return Result()

    session = Session()
    unmatched = pipeline.load_connections(
        session,
        "DOC-1",
        "7",
        [PIDConnection(from_tag="P-101", to_tag="V-301", line_type="process"),
         PIDConnection(from_tag="P-101", to_tag="MISSING-9", line_type="signal")],
        {"P-101", "V-301"},
    )

    assert unmatched == ["7: connection endpoint 'MISSING-9' (no match, P&ID)"]
    merge = [query for query, _ in session.calls if "CONNECTED_TO" in query]
    assert any("MERGE (source)-[r:CONNECTED_TO" in query for query in merge)
    assert any(params.get("source_document_id") == "DOC-1" for query, params in session.calls)


def test_build_raw_chunks_preserves_page_connections(monkeypatch):
    connection = PIDConnection(from_tag="P-101", to_tag="V-301", line_type="process")
    monkeypatch.setattr(
        pipeline,
        "vision_extract",
        lambda path, client, pages=None: [
            PIDPage(
                page_ref="3",
                page_summary="pump to valve",
                entities=[PIDEntity(tag="P-101", label="pump", symbol_type="pump")],
                connections=[connection],
            )
        ],
    )

    chunks = pipeline.build_raw_chunks(Path("drawing.pdf"), "vision", object())

    assert chunks[0].candidate_mentions == ["P-101"]
    assert chunks[0].connections == [connection]


def test_clear_connections_removes_only_document_provenance():
    class Session:
        def __init__(self):
            self.query = None
            self.params = None

        def run(self, query, **params):
            self.query, self.params = query, params

    session = Session()
    pipeline.clear_existing_connections(session, "DOC-1")

    assert "CONNECTED_TO" in session.query
    assert "source_document_id" in session.query
    assert session.params == {"source_document_id": "DOC-1"}


def test_partial_vision_ingestion_does_not_commit_full_document_hash(
    monkeypatch, tmp_path
):
    source = tmp_path / "drawing.pdf"
    source.write_bytes(b"pdf")
    calls = []

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def run(self, query, **params):
            calls.append((query, params))
            return type(
                "Result",
                (),
                {
                    "single": lambda self: None,
                    "data": lambda self: [],
                    "__iter__": lambda self: iter(()),
                },
            )()

    session = Session()
    driver = type("Driver", (), {"session": lambda self, **kwargs: session})()
    connection = PIDConnection(
        from_tag="P-101",
        to_tag="P-102",
        line_type="process",
    )

    monkeypatch.setattr(pipeline, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(pipeline, "get_driver", lambda: driver)
    monkeypatch.setattr(pipeline, "get_database", lambda: "neo4j")
    monkeypatch.setattr(pipeline, "get_gemini_client", object)
    monkeypatch.setattr(
        pipeline,
        "resolve_document",
        lambda *_args: ("DOC-PID-1", "changed"),
    )
    monkeypatch.setattr(pipeline, "route_file", lambda _path: "vision")
    monkeypatch.setattr(
        pipeline,
        "build_raw_chunks",
        lambda *_args, **_kwargs: [
            pipeline.RawChunk(
                "3",
                "P-101 to P-102",
                ["P-101", "P-102"],
                [connection],
            )
        ],
    )
    monkeypatch.setattr(
        pipeline,
        "load_known_entities",
        lambda _session: ({"P-101", "P-102"}, set()),
    )

    monkeypatch.setattr(
        pipeline,
        "index_document_chunks",
        lambda *_args, **_kwargs: 1,
    )

    result = pipeline.ingest_file(source, vision_pages=[3])

    assert result["status"] == "partial"
    assert not any("SET d.content_hash" in query for query, _ in calls)
    assert not any("DETACH DELETE c" in query for query, _ in calls)
    assert any(params.get("cid") == "DOC-PID-1-P3" for _, params in calls)
