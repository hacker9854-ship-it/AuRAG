"""BM25 keyword retrieval over Chunk text — guarantees exact-term hits
(equipment tags, clause ids) that dense/vector search can miss.

ponytail: rebuilt fresh from Neo4j on every call, not cached/persisted.
Corpus is ~17-50 Chunks; rebuild is single-digit ms. Add persistence/
incremental updates only if the corpus grows into the thousands.
"""
from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def build_bm25(session) -> tuple[BM25Okapi, list[str], list[str]]:
    """Returns (bm25, chunk_ids, texts), aligned by index."""
    records = session.run("MATCH (c:Chunk) WHERE c.text IS NOT NULL RETURN c.id AS id, c.text AS text").data()
    chunk_ids = [r["id"] for r in records]
    texts = [r["text"] for r in records]
    bm25 = BM25Okapi([_tokenize(t) for t in texts])
    return bm25, chunk_ids, texts


def search_bm25(session, query: str, top_k: int = 5) -> list[tuple[str, str, float]]:
    """Returns (chunk_id, text, score), highest score first, zero-score hits excluded."""
    bm25, chunk_ids, texts = build_bm25(session)
    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(zip(chunk_ids, texts, scores), key=lambda x: x[2], reverse=True)
    return [r for r in ranked[:top_k] if r[2] > 0]


if __name__ == "__main__":
    import truststore
    truststore.inject_into_ssl()
    from retrieval.index_chunks import get_driver, get_database

    driver, db = get_driver(), get_database()
    with driver.session(database=db) as session:
        results = search_bm25(session, "bearing lubrication", top_k=3)
    assert results, "expected at least one BM25 hit for 'bearing lubrication'"
    for cid, text, score in results:
        print(f"{score:.2f}  {cid}  {text[:80]!r}")
