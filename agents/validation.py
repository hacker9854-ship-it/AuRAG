"""Shared fail-closed helpers for command-line acceptance validators."""


def require_complete(matched: int, total: int, label: str) -> None:
    """Exit non-zero unless every required validation case passed."""
    if matched != total:
        raise SystemExit(
            f"{label} failed: {matched}/{total} required cases passed"
        )
