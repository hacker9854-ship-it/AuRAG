"""Qdrant dense-vector store wrapper. Local Docker only (infra/docker-compose.yml),
complements the Neo4j native vector index per PRD's architecture diagram —
both are queried, not one standing in for the other."""
import os
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

COLLECTION = "chunks"
EMBED_DIM = 384  # all-MiniLM-L6-v2 output dimension

_client = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(
            url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
            api_key=os.environ.get("QDRANT_API_KEY") or None,
            timeout=2.0,
        )
    return _client



def ensure_collection() -> None:
    client = get_client()
    if not client.collection_exists(COLLECTION):
        client.create_collection(COLLECTION, vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE))


def upsert_chunks(items: list[tuple[str, list[float], str]]) -> None:
    """items: (chunk_id, vector, text)."""
    ensure_collection()
    points = [
        PointStruct(id=_point_id(cid), vector=vec, payload={"chunk_id": cid, "text": text})
        for cid, vec, text in items
    ]
    get_client().upsert(COLLECTION, points=points)


def search(query_vector: list[float], top_k: int = 5) -> list[tuple[str, str, float]]:
    """Returns (chunk_id, text, score), highest score first."""
    ensure_collection()
    hits = get_client().query_points(COLLECTION, query=query_vector, limit=top_k).points
    return [(h.payload["chunk_id"], h.payload["text"], h.score) for h in hits]


def _point_id(chunk_id: str) -> str:
    # ponytail: Qdrant point ids must be uint or UUID, not arbitrary strings
    # like "DOC-...-C001" — deterministic UUID5 keeps upserts idempotent.
    import uuid
    return str(uuid.uuid5(uuid.NAMESPACE_OID, chunk_id))


if __name__ == "__main__":
    from retrieval.embeddings import embed_texts

    vecs = embed_texts(["pump bearing failure", "relief valve calibration"])
    upsert_chunks([("SELFTEST-1", vecs[0], "pump bearing failure"), ("SELFTEST-2", vecs[1], "relief valve calibration")])
    results = search(vecs[0], top_k=2)
    assert results[0][0] == "SELFTEST-1", results
    print(f"OK: top hit = {results[0][0]} (score={results[0][2]:.3f})")
