"""Dependency health aggregation without framework or provider coupling."""

from collections.abc import Callable, Mapping
from typing import Any


HealthCheck = Callable[[], Any]


def build_readiness(checks: Mapping[str, HealthCheck]) -> dict:
    dependencies: dict[str, dict[str, str]] = {}
    ready = True

    for name, check in checks.items():
        try:
            check()
            dependencies[name] = {"status": "up"}
        except Exception as exc:
            ready = False
            dependencies[name] = {"status": "down", "detail": str(exc)}

    return {
        "status": "ready" if ready else "degraded",
        "ready": ready,
        "dependencies": dependencies,
    }

