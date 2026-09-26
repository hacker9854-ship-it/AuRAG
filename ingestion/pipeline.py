"""The convergence step (PRD Section 8, feature #1): every ingestion path —
clean text, OCR, P&ID vision — ends up here. Owns the one Neo4j driver, the
one Gemini client, chunk creation, entity extraction, closed-world fuzzy
matching, and MERGE-based idempotent loading.

Usage: ingest_file(path) -> summary dict. See cli.py for the entry point.
"""
import difflib
import hashlib
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Literal

import truststore  # ponytail: same OpenSSL 3.x chain-building bug as load_seed.py
truststore.inject_into_ssl()

from dotenv import load_dotenv
from google import genai
from google.genai import types
from neo4j import GraphDatabase
from pydantic import BaseModel

from ingestion.gemini_util import throttled_generate
from ingestion.parsers.clean_text import classify_pdf, parse_clean_text
from ingestion.parsers.ocr import transcribe as ocr_transcribe
from ingestion.parsers.vision_pnid import PIDConnection, extract as vision_extract

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

GEMINI_MODEL = os.environ.get(
    "GEMINI_INGESTION_MODEL",
    "gemini-3.1-flash-lite",
)

_driver = None
_gemini_client = None


def get_driver():
    global _driver
    if _driver is None:
        uri, user, pwd = (os.environ.get(k) for k in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"))
        if not all([uri, user, pwd]):
            print("Missing NEO4J_URI/NEO4J_USERNAME/NEO4J_PASSWORD in .env", file=sys.stderr)
            sys.exit(1)
        _driver = GraphDatabase.driver(uri, auth=(user, pwd))
        _driver.verify_connectivity()
    return _driver


def get_database() -> str:
    return os.environ.get("NEO4J_DATABASE", "neo4j")


def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Missing GEMINI_API_KEY in .env", file=sys.stderr)
            sys.exit(1)
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


# --- Entity extraction (LLM structured JSON output, per PRD Section 5) -----

class Mention(BaseModel):
    raw_text: str
    entity_type: Literal["equipment", "person"]


class ExtractionResult(BaseModel):
    mentions: list[Mention]


def extract_entities_llm(client, text: str) -> list[Mention]:
    if not text.strip():
        return []
    prompt = (
        "Extract every equipment tag and person name mentioned in this "
        "industrial maintenance text.\n"
        "Equipment tags identify physical plant equipment, e.g. P-101, "
        "PSV-701, HX-401 (equipment-class prefix + dash + digits; common "
        "prefixes: P, C, V, PSV, HX, T, R, FCV, CV, MOT, TK).\n"
        "Do NOT extract FE-xxx (FailureEvent ids), WO-xxx (WorkOrder ids), "
        "DOC-xxx (Document ids), or PROC-xxx (Procedure ids) as equipment "
        "— those are event/record identifiers, not physical equipment, "
        "even though they share a similar dash-separated format.\n"
        "Person names are proper names of plant personnel, not generic role "
        "titles.\n\nText:\n" + text
    )
    response = throttled_generate(
        client,
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractionResult,
        ),
    )
    return ExtractionResult.model_validate_json(response.text).mentions


# --- Closed-world fuzzy matching (never creates new nodes) ------------------

_DIGIT_OCR_FIX = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "S": "5", "s": "5", "B": "8"})
_TAG_RE = re.compile(r"^[A-Z]+-\d+$")


def normalize_equipment_tag(raw: str) -> str | None:
    s = raw.strip().upper().replace(" ", "")
    if "-" not in s:
        return None
    prefix, _, suffix = s.rpartition("-")
    candidate = f"{prefix}-{suffix.translate(_DIGIT_OCR_FIX)}"
    return candidate if _TAG_RE.match(candidate) else None


def match_equipment(raw: str, known_tags: set[str]) -> str | None:
    normalized = normalize_equipment_tag(raw)
    if normalized is None:
        return None
    if normalized in known_tags:
        return normalized
    close = difflib.get_close_matches(normalized, known_tags, n=1, cutoff=0.8)
    return close[0] if close else None


def match_person(raw: str, known_names: set[str]) -> str | None:
    raw_norm = " ".join(raw.strip().split())
    lower_map = {n.lower(): n for n in known_names}
    if raw_norm.lower() in lower_map:
        return lower_map[raw_norm.lower()]
    close = difflib.get_close_matches(raw_norm.lower(), lower_map.keys(), n=1, cutoff=0.8)
    return lower_map[close[0]] if close else None


def load_known_entities(session) -> tuple[set[str], set[str]]:
    tags = {r["t"] for r in session.run("MATCH (e:Equipment) RETURN e.tag_id AS t")}
    names = {r["n"] for r in session.run("MATCH (p:Person) RETURN p.name AS n")}
    return tags, names


# --- Document resolution / idempotent dedup ---------------------------------

def resolve_document(session, path: Path, content_hash: str) -> tuple[str, Literal["new", "changed", "unchanged"]]:
    rel = path.relative_to(REPO_ROOT).as_posix()
    rec = session.run(
        "MATCH (d:Document {source_file:$sf}) RETURN d.id AS id, d.content_hash AS hash",
        sf=rel,
    ).single()
    if rec is None:
        slug = re.sub(r"[^A-Za-z0-9]+", "-", path.stem).strip("-").upper()[:20]
        return f"DOC-{slug}-{content_hash[:8]}", "new"
    if rec["hash"] == content_hash:
        return rec["id"], "unchanged"
    return rec["id"], "changed"


_ROUTE_DOC_TYPE = {"clean_text": "Text Document", "ocr": "Scanned Document", "vision": "Diagram"}


def upsert_new_document(session, doc_id: str, path: Path, route: str) -> None:
    rel = path.relative_to(REPO_ROOT).as_posix()
    session.run(
        """
        MERGE (d:Document {id:$id})
        SET d.type = $type, d.title = $title, d.date = $date, d.source_file = $sf
        """,
        id=doc_id,
        type=_ROUTE_DOC_TYPE[route],
        title=path.stem.replace("_", " ").replace("-", " ").title(),
        date=date.today().isoformat(),
        sf=rel,
    )


def clear_existing_chunks(session, doc_id: str) -> None:
    session.run("MATCH (:Document {id:$id})-[:CONTAINS]->(c:Chunk) DETACH DELETE c", id=doc_id)


def clear_existing_connections(session, doc_id: str) -> None:
    session.run(
        "MATCH ()-[r:CONNECTED_TO {source_document_id:$source_document_id}]->() DELETE r",
        source_document_id=doc_id,
    )


def clear_page_connections(session, doc_id: str, page_ref: str) -> None:
    session.run(
        """
        MATCH ()-[r:CONNECTED_TO {
          source_document_id:$source_document_id,
          page_ref:$page_ref
        }]->()
        DELETE r
        """,
        source_document_id=doc_id,
        page_ref=page_ref,
    )


def load_chunk(session, doc_id: str, chunk_id: str, page_ref: str, text: str, mentions: list[tuple[str, str]]) -> None:
    session.run(
        """
        MERGE (c:Chunk {id:$cid})
        SET c.text = $text, c.page_ref = $page_ref
        WITH c
        OPTIONAL MATCH (c)-[old:MENTIONS]->()
        DELETE old
        WITH c
        MATCH (d:Document {id:$did})
        MERGE (d)-[:CONTAINS]->(c)
        """,
        cid=chunk_id, text=text, page_ref=page_ref, did=doc_id,
    )
    for label, key in mentions:
        if label == "Equipment":
            session.run(
                "MATCH (c:Chunk {id:$cid}), (e:Equipment {tag_id:$key}) MERGE (c)-[:MENTIONS]->(e)",
                cid=chunk_id, key=key,
            )
        else:
            session.run(
                "MATCH (c:Chunk {id:$cid}), (p:Person {name:$key}) MERGE (c)-[:MENTIONS]->(p)",
                cid=chunk_id, key=key,
            )


def set_document_hash(session, doc_id: str, content_hash: str) -> None:
    session.run("MATCH (d:Document {id:$id}) SET d.content_hash = $hash", id=doc_id, hash=content_hash)


def index_document_chunks(session, chunk_ids: list[str]) -> int:
    from retrieval.index_chunks import index_chunks

    return index_chunks(session, chunk_ids=chunk_ids)


class ConnectionLoadReport(list[str]):
    def __init__(self, unmatched: list[str], loaded_count: int):
        super().__init__(unmatched)
        self.loaded_count = loaded_count


def load_connections(
    session,
    doc_id: str,
    page_ref: str,
    connections: list[PIDConnection],
    known_tags: set[str],
) -> ConnectionLoadReport:
    loaded = 0
    unmatched: list[str] = []
    for connection in connections:
        from_tag = match_equipment(connection.from_tag, known_tags)
        to_tag = match_equipment(connection.to_tag, known_tags)
        if from_tag is None:
            unmatched.append(
                f"{page_ref}: connection endpoint '{connection.from_tag}' (no match, P&ID)"
            )
        if to_tag is None:
            unmatched.append(
                f"{page_ref}: connection endpoint '{connection.to_tag}' (no match, P&ID)"
            )
        if from_tag is None or to_tag is None:
            continue
        session.run(
            """
            MATCH (source:Equipment {tag_id:$from_tag})
            MATCH (target:Equipment {tag_id:$to_tag})
            MERGE (source)-[r:CONNECTED_TO {
                line_type:$line_type,
                source_document_id:$source_document_id,
                page_ref:$page_ref
            }]->(target)
            """,
            from_tag=from_tag,
            to_tag=to_tag,
            line_type=connection.line_type,
            source_document_id=doc_id,
            page_ref=page_ref,
        )
        loaded += 1
    return ConnectionLoadReport(unmatched, loaded)


# --- Routing: directory-first for the known seed corpus, extension/heuristic
# fallback for anything new (continuous-ingestion drops into data/incoming/) --

def route_file(path: Path) -> Literal["clean_text", "ocr", "vision"]:
    parts = path.relative_to(REPO_ROOT).parts
    if "documents" in parts:
        return "clean_text"
    if "scanned" in parts:
        return "ocr"
    if "pnid" in parts:
        return "vision"

    suffix = path.suffix.lower()
    if suffix in (".md", ".txt"):
        return "clean_text"
    if suffix in (".jpg", ".jpeg", ".png"):
        return "ocr"
    if suffix == ".pdf":
        return "clean_text" if classify_pdf(path) == "text" else "vision"
    raise ValueError(f"route_file: cannot route {path} (unknown extension {suffix!r})")


@dataclass
class RawChunk:
    page_ref: str
    text: str
    candidate_mentions: list[str] | None = None  # None => run LLM extraction; else use directly (P&ID tags)
    connections: list[PIDConnection] = field(default_factory=list)


def build_raw_chunks(path: Path, route: str, client, vision_pages: list[int] | None = None) -> list[RawChunk]:
    if route == "clean_text":
        return [RawChunk(ref, text) for ref, text in parse_clean_text(path)]
    if route == "ocr":
        result = ocr_transcribe(path, client)
        text, used_fallback = result
        print(f"   ocr: engine = {result.engine}; mean-conf fallback used = {used_fallback}")
        return [RawChunk("1", text)]
    if route == "vision":
        chunks = []
        for page in vision_extract(path, client, pages=vision_pages):
            chunks.append(RawChunk(
                page.page_ref,
                page.page_summary,
                [e.tag for e in page.entities],
                page.connections,
            ))
        return chunks
    raise ValueError(f"unknown route {route!r}")


def ingest_file(path: Path, vision_pages: list[int] | None = None) -> dict:
    """vision_pages: for the P&ID route only — limit which pages Gemini
    vision processes (e.g. for dev/test runs on a tight API quota). None
    (default) processes every page, which is correct for real ingestion."""
    path = path.resolve()
    content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    driver, db = get_driver(), get_database()
    client = get_gemini_client()

    with driver.session(database=db) as session:
        doc_id, status = resolve_document(session, path, content_hash)
        print(f"-- {path.relative_to(REPO_ROOT)} -> {doc_id} ({status})")

        route = route_file(path)
        partial_vision = route == "vision" and vision_pages is not None

        if status == "unchanged" and not partial_vision:
            return {"doc_id": doc_id, "status": status, "chunks": 0, "mentions": 0, "unmatched": []}

        # Parse/extract first. A provider failure must leave the previously
        # accepted document graph intact so the same file can be retried.
        raw_chunks = build_raw_chunks(path, route, client, vision_pages=vision_pages)

        if status == "new":
            upsert_new_document(session, doc_id, path, route)
        elif not partial_vision:
            clear_existing_chunks(session, doc_id)
            clear_existing_connections(session, doc_id)

        known_tags, known_names = load_known_entities(session)
        total_mentions = 0
        total_connections = 0
        unmatched: list[str] = []
        chunk_ids: list[str] = []

        for i, rc in enumerate(raw_chunks, start=1):
            if route == "vision":
                page_token = re.sub(r"[^A-Za-z0-9]+", "-", rc.page_ref).strip("-")
                chunk_id = f"{doc_id}-P{page_token}"
                if partial_vision:
                    clear_page_connections(session, doc_id, rc.page_ref)
            else:
                chunk_id = f"{doc_id}-C{i:03d}"
            chunk_ids.append(chunk_id)
            resolved: list[tuple[str, str]] = []

            if rc.candidate_mentions is None:
                mentions = extract_entities_llm(client, rc.text)
                for m in mentions:
                    if m.entity_type == "equipment":
                        hit = match_equipment(m.raw_text, known_tags)
                        if hit:
                            resolved.append(("Equipment", hit))
                        else:
                            unmatched.append(f"{chunk_id}: equipment '{m.raw_text}' (no match)")
                    else:
                        hit = match_person(m.raw_text, known_names)
                        if hit:
                            resolved.append(("Person", hit))
                        else:
                            unmatched.append(f"{chunk_id}: person '{m.raw_text}' (no match)")
            else:
                for raw_tag in rc.candidate_mentions:
                    hit = match_equipment(raw_tag, known_tags)
                    if hit:
                        resolved.append(("Equipment", hit))
                    else:
                        unmatched.append(f"{chunk_id}: equipment '{raw_tag}' (no match, P&ID)")

            resolved = sorted(set(resolved))
            load_chunk(session, doc_id, chunk_id, rc.page_ref, rc.text, resolved)
            total_mentions += len(resolved)
            connection_report = load_connections(
                session, doc_id, rc.page_ref, rc.connections, known_tags
            )
            total_connections += connection_report.loaded_count
            unmatched.extend(f"{chunk_id}: {message}" for message in connection_report)

        index_document_chunks(session, chunk_ids)
        # Commit the content hash only after both Neo4j embedding writes and
        # Qdrant upsert succeed. If vector indexing fails, the old hash keeps
        # the document retryable instead of incorrectly marking it unchanged.
        if not partial_vision:
            set_document_hash(session, doc_id, content_hash)

    summary = {
        "doc_id": doc_id,
        "status": "partial" if partial_vision else status,
        "chunks": len(raw_chunks),
        "mentions": total_mentions, "connections": total_connections,
        "unmatched": unmatched,
    }
    print(f"   {summary['chunks']} chunk(s), {summary['mentions']} mention(s) linked, "
          f"{summary['connections']} connection(s) linked, {len(unmatched)} unmatched")
    for u in unmatched:
        print(f"   ! unmatched: {u}")
    return summary
