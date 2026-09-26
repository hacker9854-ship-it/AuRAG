"""Fuses the four retrieval sources (Neo4j native vector, Qdrant dense, BM25
keyword, graph traversal) and reranks with a local cross-encoder. Per PRD
Section 14: each source is validated independently (see each module's
__main__ self-check) before being combined here.

Usage: retrieve(session, query) -> [(key, text, score), ...]
"""
from retrieval import qdrant_store
from retrieval.bm25_index import search_bm25
from retrieval.candidate_filter import (
    filter_to_explicit_anchors,
    filter_to_explicit_years,
)
from retrieval.embeddings import embed_texts
from retrieval.graph_traversal import extract_query_entities, traverse
from ingestion.pipeline import load_known_entities
from retrieval.rerank import rerank

_CANDIDATES_PER_SOURCE = 10

# ponytail: db.index.vector.queryNodes is deprecated in favor of a newer
# SEARCH syntax on some Neo4j 5.x builds, but still functions (warning only,
# not an error) — not worth chasing a moving-target syntax mid-hackathon.
_NEO4J_VECTOR_CYPHER = """
CALL db.index.vector.queryNodes('chunk_embedding', $k, $vec)
YIELD node, score
RETURN node.id AS id, node.text AS text, score
"""


def _neo4j_vector_search(session, query_vec: list[float], top_k: int) -> list[tuple[str, str]]:
    rows = session.run(_NEO4J_VECTOR_CYPHER, k=top_k, vec=query_vec).data()
    return [(r["id"], r["text"]) for r in rows if r["text"]]


def retrieve(session, query: str, top_k: int = 5) -> list[tuple[str, str, float]]:
    query_vec = embed_texts([query])[0]

    candidates: dict[str, str] = {}

    try:
        for key, text in _neo4j_vector_search(session, query_vec, _CANDIDATES_PER_SOURCE):
            candidates[key] = text
    except Exception:
        pass

    try:
        for key, text, _ in qdrant_store.search(query_vec, top_k=_CANDIDATES_PER_SOURCE):
            candidates[key] = text
    except Exception:
        pass

    try:
        for key, text, _ in search_bm25(session, query, top_k=_CANDIDATES_PER_SOURCE):
            candidates[key] = text
    except Exception:
        pass

    graph_candidates = []
    try:
        graph_candidates = traverse(session, query, top_k=_CANDIDATES_PER_SOURCE)
        for key, text in graph_candidates:
            candidates[key] = text
    except Exception:
        pass

    try:
        known_tags, known_names = load_known_entities(session)
        tags, names = extract_query_entities(query, known_tags, known_names)
        candidates = filter_to_explicit_anchors(
            candidates,
            graph_candidates,
            [*tags, *names],
        )
    except Exception:
        pass

    candidates = filter_to_explicit_years(candidates, query)

    if not candidates:
        return []

    return rerank(query, list(candidates.items()), top_n=top_k)


if __name__ == "__main__":
    import truststore
    truststore.inject_into_ssl()
    from retrieval.index_chunks import get_driver, get_database

    driver, db = get_driver(), get_database()
    with driver.session(database=db) as session:
        results = retrieve(session, "Why did P-101 fail in March 2025?")
    assert results, "expected fused hits for a P-101 query"
    for key, text, score in results:
        print(f"{score:.2f}  {key}  {text[:80]!r}")
