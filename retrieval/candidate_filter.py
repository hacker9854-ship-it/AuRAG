"""Pure candidate filtering helpers for entity-anchored retrieval."""

import re

_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_SHORT_DATE_RE = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-](\d{2})\b")


def _extract_years(text: str) -> set[str]:
    years = set(_YEAR_RE.findall(text))
    for short_year in _SHORT_DATE_RE.findall(text):
        value = int(short_year)
        years.add(str(2000 + value if value < 70 else 1900 + value))
    return years


def filter_to_explicit_anchors(
    candidates: dict[str, str],
    graph_candidates: list[tuple[str, str]],
    anchors: list[str],
) -> dict[str, str]:
    """Remove cross-entity noise when the query names a known entity."""
    if not anchors:
        return candidates

    graph_keys = {key for key, _ in graph_candidates}
    lowered_anchors = [anchor.casefold() for anchor in anchors]
    return {
        key: text
        for key, text in candidates.items()
        if key in graph_keys
        or any(anchor in text.casefold() for anchor in lowered_anchors)
    }


def filter_to_explicit_years(
    candidates: dict[str, str],
    query: str,
) -> dict[str, str]:
    """Drop records with an explicit year that conflicts with the query."""
    query_years = _extract_years(query)
    if not query_years:
        return candidates

    filtered = {}
    for key, text in candidates.items():
        candidate_years = _extract_years(text)
        if not candidate_years or candidate_years & query_years:
            filtered[key] = text
    return filtered
