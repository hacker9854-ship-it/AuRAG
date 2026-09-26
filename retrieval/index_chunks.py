"""Embeds Chunk.text and writes it back as Chunk.embedding (Neo4j native
vector index) + upserts into Qdrant. One function, two call sites: a one-time
full backfill (chunk_ids=None) and an incremental call from
ingestion.pipeline.ingest_file() so continuous ingestion stays current.

Usage: python -m retrieval.index_chunks   (full backfill)
"""
import os
import sys
from pathlib import Path

import truststore
truststore.inject_into_ssl()

from dotenv import load_dotenv
from neo4j import GraphDatabase

from retrieval.embeddings import embed_texts
from retrieval.qdrant_store import upsert_chunks

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        uri, user, pwd = (os.environ.get(k) for k in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"))
        if not all([uri, user, pwd]):
            raise RuntimeError("Missing NEO4J_URI/NEO4J_USERNAME/NEO4J_PASSWORD in environment")
        _driver = GraphDatabase.driver(uri, auth=(user, pwd), connection_timeout=5.0, max_connection_lifetime=300)
    return _driver



def get_database() -> str | None:
    db = os.environ.get("NEO4J_DATABASE")
    if not db or db in ("neo4j", "None", ""):
        user = os.environ.get("NEO4J_USERNAME")
        if user and user != "neo4j":
            return user
        return None
    return db



def index_chunks(session, chunk_ids: list[str] | None = None) -> int:
    """Embed Chunk.text for the given ids (or every Chunk if None), write
    Chunk.embedding in Neo4j, and upsert the same vectors into Qdrant."""
    if chunk_ids is None:
        records = session.run("MATCH (c:Chunk) RETURN c.id AS id, c.text AS text").data()
    else:
        records = session.run(
            "MATCH (c:Chunk) WHERE c.id IN $ids RETURN c.id AS id, c.text AS text",
            ids=chunk_ids,
        ).data()
    records = [r for r in records if r["text"]]
    if not records:
        return 0

    vectors = embed_texts([r["text"] for r in records])
    for rec, vec in zip(records, vectors):
        session.run("MATCH (c:Chunk {id:$id}) SET c.embedding = $vec", id=rec["id"], vec=vec)

    upsert_chunks([(r["id"], vec, r["text"]) for r, vec in zip(records, vectors)])
    return len(records)


if __name__ == "__main__":
    driver, db = get_driver(), get_database()
    with driver.session(database=db) as session:
        n = index_chunks(session)
    print(f"Indexed {n} chunk(s) (Neo4j vector index + Qdrant).")
