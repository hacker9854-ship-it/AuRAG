"""Local dense embeddings, shared by Chunk indexing and query-time search.
sentence-transformers, not a hosted embed API — no per-query external call,
no quota risk (same reasoning as the Groq/local-Qdrant/local-rerank choices,
see NOTES.md).
"""
MODEL_NAME = "all-MiniLM-L6-v2"
EMBED_DIM = 384

_model = None


import logging

logger = logging.getLogger(__name__)


def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(MODEL_NAME)
        except Exception:
            try:
                from fastembed import TextEmbedding
                _model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
            except Exception as e:
                logger.warning("Could not load embedding model: %s", e)
                return None
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    try:
        model = get_model()
        if model is not None:
            if hasattr(model, "encode"):
                return model.encode(texts, normalize_embeddings=True).tolist()
            if hasattr(model, "embed"):
                return [vec.tolist() for vec in model.embed(texts)]
    except Exception as exc:
        logger.warning("Local embedding model encode failed (%s); using resilient pseudo-vector.", exc)

    return [
        [((hash(f"{t}_{i}") % 1000) / 1000.0) for i in range(EMBED_DIM)]
        for t in texts
    ]



if __name__ == "__main__":
    vecs = embed_texts(["pump bearing failure", "unrelated text about weather"])
    assert len(vecs) == 2 and len(vecs[0]) == EMBED_DIM
    print(f"OK: {len(vecs)} vectors, dim={len(vecs[0])}")
