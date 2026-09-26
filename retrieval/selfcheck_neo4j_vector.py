"""Standalone isolation self-check for the Neo4j native vector index only
(no Qdrant, no BM25, no graph traversal) — per PRD Section 14's requirement
to test each retrieval path independently before combining."""
import truststore
truststore.inject_into_ssl()

from retrieval.hybrid import _neo4j_vector_search
from retrieval.index_chunks import get_driver, get_database
from retrieval.embeddings import embed_texts


def main() -> None:
    driver, db = get_driver(), get_database()
    query = "Why did P-101 fail in March 2025?"
    vec = embed_texts([query])[0]

    with driver.session(database=db) as session:
        rows = _neo4j_vector_search(session, vec, top_k=5)

    driver.close()

    assert rows, "expected Neo4j-vector-only hits for a P-101 query"
    for key, text in rows:
        print(f"{key}  {text[:70]!r}")
    print("OK: Neo4j vector-only self-check passed in isolation")


if __name__ == "__main__":
    main()
