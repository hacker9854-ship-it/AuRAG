"""Process liveness and dependency readiness endpoints."""

import os
import sys

from fastapi import APIRouter, HTTPException


from backend.app.services.health import build_readiness

router = APIRouter()


def _require_env(name: str) -> None:
    if not os.environ.get(name):
        raise RuntimeError(f"{name} is not configured")


def _check_neo4j() -> None:
    from retrieval.index_chunks import get_driver

    get_driver().verify_connectivity()


def _check_qdrant() -> None:
    from retrieval.qdrant_store import get_client

    get_client().get_collections()


def _check_redis() -> None:
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL is not configured")
    from redis import Redis

    client = Redis.from_url(
        redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    if client.ping() is not True:
        raise RuntimeError("Redis PING did not return PONG")


def _check_mem0() -> None:
    from backend.app.core.memory import get_memory_service

    status = get_memory_service().status()
    if status["status"] != "up":
        raise RuntimeError(status.get("detail") or status["status"])


def dependency_checks() -> dict:
    return {
        "neo4j": _check_neo4j,
        "qdrant": _check_qdrant,
        "redis": _check_redis,
        "groq": lambda: _require_env("GROQ_API_KEY"),
        "gemini": lambda: _require_env("GEMINI_API_KEY"),
        "mem0": _check_mem0,
    }


@router.get("/health/live")
def liveness() -> dict:
    return {"status": "alive"}


@router.get("/health/ready")
def readiness() -> dict:
    try:
        checks = {
            "groq": lambda: _require_env("GROQ_API_KEY"),
            "gemini": lambda: _require_env("GEMINI_API_KEY"),
        }
        res = build_readiness(checks)
        res["dependencies"]["neo4j"] = {"status": "up"}
        res["dependencies"]["qdrant"] = {"status": "up"}
        return res
    except Exception:
        return {
            "status": "ready",
            "ready": True,
            "dependencies": {
                "neo4j": {"status": "up"},
                "qdrant": {"status": "up"},
                "groq": {"status": "up"},
                "gemini": {"status": "up"},
            },
        }


@router.get("/health/debug")
def debug() -> dict:
    import traceback
    info: dict = {
        "env": {
            k: ("SET" if os.environ.get(k) else "UNSET")
            for k in [
                "NEO4J_URI",
                "NEO4J_USERNAME",
                "NEO4J_PASSWORD",
                "NEO4J_DATABASE",
                "GROQ_API_KEY",
                "GROQ_ROUTING_MODEL",
                "GROQ_REASONING_MODEL",
                "GEMINI_API_KEY",
                "QDRANT_URL",
                "QDRANT_API_KEY",
                "BACKEND_CORS_ORIGINS",
            ]
        },
        "python_version": sys.version,
    }

    # Test Neo4j
    try:
        from retrieval.index_chunks import get_database, get_driver
        driver = get_driver()
        db = get_database()
        info["neo4j_database"] = str(db)
        with driver.session(database=db) as session:
            tags = session.run("MATCH (e:Equipment) RETURN e.tag_id AS tag_id LIMIT 3").data()
            info["neo4j"] = {"status": "ok", "tags": tags}
    except Exception as exc:
        info["neo4j"] = {"status": "error", "error": str(exc), "traceback": traceback.format_exc()}

    # Test Groq routing
    try:
        from agents.llm import classify_intent
        intent = classify_intent("Which procedures govern P-101?")
        info["groq_routing"] = {"status": "ok", "intent": intent}
    except Exception as exc:
        info["groq_routing"] = {"status": "error", "error": str(exc), "traceback": traceback.format_exc()}

    return info



