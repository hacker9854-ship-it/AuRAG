"""Dense-vector-only retrieval baseline used by the comparison feature."""

from collections.abc import Callable


def retrieve(
    query: str,
    top_k: int = 5,
    *,
    embed_fn: Callable | None = None,
    search_fn: Callable | None = None,
) -> list[tuple[str, str, float]]:
    if embed_fn is None:
        from retrieval.embeddings import embed_texts

        embed_fn = embed_texts
    if search_fn is None:
        from retrieval.qdrant_store import search

        search_fn = search

    query_vector = embed_fn([query])[0]
    return search_fn(query_vector, top_k=top_k)

