"""Configurable Cohere or local cross-encoder candidate reranking."""

import os

LOCAL_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
COHERE_MODEL = os.environ.get("COHERE_RERANK_MODEL", "rerank-v4.0-pro")

_local_model = None
_cohere_client = None


def get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import CrossEncoder

        _local_model = CrossEncoder(LOCAL_MODEL_NAME)
    return _local_model


def get_cohere_client():
    global _cohere_client
    if _cohere_client is None:
        import cohere

        api_key = os.environ.get("COHERE_API_KEY")
        if not api_key:
            raise RuntimeError("COHERE_API_KEY is required when RERANK_PROVIDER=cohere")
        _cohere_client = cohere.ClientV2(api_key=api_key)
    return _cohere_client


def _rerank_local(
    query: str,
    candidates: list[tuple[str, str]],
    top_n: int,
) -> list[tuple[str, str, float]]:
    pairs = [(query, text) for _, text in candidates]
    scores = get_local_model().predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda item: item[1], reverse=True)
    return [
        (key, text, float(score))
        for (key, text), score in ranked[:top_n]
    ]


def _rerank_cohere(
    query: str,
    candidates: list[tuple[str, str]],
    top_n: int,
) -> list[tuple[str, str, float]]:
    response = get_cohere_client().rerank(
        model=COHERE_MODEL,
        query=query,
        documents=[text for _, text in candidates],
        top_n=min(top_n, len(candidates)),
    )
    return [
        (
            candidates[result.index][0],
            candidates[result.index][1],
            float(result.relevance_score),
        )
        for result in response.results
    ]


def rerank(
    query: str,
    candidates: list[tuple[str, str]],
    top_n: int = 5,
) -> list[tuple[str, str, float]]:
    if not candidates:
        return []
    provider = os.environ.get("RERANK_PROVIDER", "local").lower()
    if provider == "cohere":
        return _rerank_cohere(query, candidates, top_n)
    if provider == "local":
        return _rerank_local(query, candidates, top_n)
    raise ValueError(f"Unsupported RERANK_PROVIDER: {provider}")


if __name__ == "__main__":
    candidates = [
        ("A", "Relief valve calibration is checked annually per OISD standard."),
        ("B", "The cafeteria menu changes every Tuesday."),
    ]
    results = rerank("What is the relief valve calibration requirement?", candidates)
    assert results[0][0] == "A", results
    print(f"OK: top hit = {results[0][0]} (score={results[0][2]:.3f})")
