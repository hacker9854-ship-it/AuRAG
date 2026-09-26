from retrieval.plain_vector import retrieve


def test_plain_vector_uses_only_dense_embedding_and_qdrant_search():
    calls = []

    def embed(texts):
        calls.append(("embed", texts))
        return [[0.1, 0.2]]

    def search(vector, top_k):
        calls.append(("qdrant", vector, top_k))
        return [
            ("CHUNK-2", "second result", 0.82),
            ("CHUNK-1", "first result", 0.91),
        ]

    result = retrieve("Why did P-101 fail?", top_k=2, embed_fn=embed, search_fn=search)

    assert calls == [
        ("embed", ["Why did P-101 fail?"]),
        ("qdrant", [0.1, 0.2], 2),
    ]
    assert result == [
        ("CHUNK-2", "second result", 0.82),
        ("CHUNK-1", "first result", 0.91),
    ]

