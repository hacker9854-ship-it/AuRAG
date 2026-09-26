from backend.app.services.health import build_readiness


def test_readiness_reports_each_dependency_independently():
    checks = {
        "neo4j": lambda: None,
        "qdrant": lambda: (_ for _ in ()).throw(ConnectionError("offline")),
        "redis": lambda: None,
        "groq": lambda: None,
        "gemini": lambda: (_ for _ in ()).throw(RuntimeError("missing key")),
        "mem0": lambda: None,
    }

    result = build_readiness(checks)

    assert result["status"] == "degraded"
    assert result["ready"] is False
    assert result["dependencies"]["neo4j"] == {"status": "up"}
    assert result["dependencies"]["qdrant"] == {
        "status": "down",
        "detail": "offline",
    }
    assert result["dependencies"]["gemini"]["status"] == "down"


def test_readiness_is_ready_only_when_every_required_check_passes():
    result = build_readiness({"neo4j": lambda: None, "redis": lambda: True})

    assert result == {
        "status": "ready",
        "ready": True,
        "dependencies": {
            "neo4j": {"status": "up"},
            "redis": {"status": "up"},
        },
    }


def test_health_api_liveness_is_process_only():
    from backend.app.api.health import liveness

    assert liveness() == {"status": "alive"}


def test_health_api_readiness_returns_503_when_dependencies_are_down(monkeypatch):
    from fastapi import HTTPException

    from backend.app.api import health

    monkeypatch.setattr(
        health,
        "dependency_checks",
        lambda: {
            "neo4j": lambda: None,
            "redis": lambda: (_ for _ in ()).throw(ConnectionError("refused")),
        },
    )

    try:
        health.readiness()
    except HTTPException as exc:
        assert exc.status_code == 503
        assert exc.detail["status"] == "degraded"
        assert exc.detail["dependencies"]["redis"]["detail"] == "refused"
    else:
        raise AssertionError("readiness should return HTTP 503 when a dependency is down")


def test_cors_origins_are_read_from_environment(monkeypatch):
    from backend.app import main

    monkeypatch.setenv(
        "BACKEND_CORS_ORIGINS",
        "https://aurag.example, https://preview.example/ ",
    )

    assert main.cors_origins() == [
        "https://aurag.example",
        "https://preview.example",
    ]


def test_redis_readiness_uses_ping(monkeypatch):
    from backend.app.api import health

    calls = {}

    class Client:
        def ping(self):
            calls["ping"] = True
            return True

    monkeypatch.setattr(
        "redis.Redis.from_url",
        lambda url, **kwargs: calls.update(url=url, kwargs=kwargs) or Client(),
    )

    health._check_redis()

    assert calls["ping"] is True
    assert calls["url"].startswith("redis://")


def test_qdrant_readiness_uses_authenticated_client(monkeypatch):
    from backend.app.api import health

    calls = {}

    class Client:
        def get_collections(self):
            calls["get_collections"] = True

    monkeypatch.setattr("retrieval.qdrant_store.get_client", lambda: Client())

    health._check_qdrant()

    assert calls["get_collections"] is True
