"""Path 3: P&ID / engineering drawings. Gemini vision extracts equipment
symbols, labels, and connections per page (PRD Section 8, feature #1).

`connections` are returned with page provenance and the ingestion pipeline
persists matching endpoints as CONNECTED_TO relationships. Unmatched diagram
tags remain explicit in the ingestion report rather than creating phantom
equipment nodes.
not write them as graph edges (see NOTES.md scope boundary). `entities`
(via `.tag`) flow into the same closed-world fuzzy-match step as every
other path.
"""
import os
from pathlib import Path

from google.genai import types
from pydantic import BaseModel

from ingestion.gemini_util import throttled_generate

GEMINI_MODEL = os.environ.get(
    "GEMINI_INGESTION_MODEL",
    "gemini-3.1-flash-lite",
)


class PIDEntity(BaseModel):
    tag: str
    label: str
    symbol_type: str


class PIDConnection(BaseModel):
    from_tag: str
    to_tag: str
    line_type: str


class PIDExtraction(BaseModel):
    entities: list[PIDEntity]
    connections: list[PIDConnection]
    page_summary: str


class PIDConnectionAudit(BaseModel):
    """Independent, connection-only visual pass for dense P&ID pages."""

    connections: list[PIDConnection]


class PIDPage(BaseModel):
    page_ref: str
    page_summary: str
    entities: list[PIDEntity]
    connections: list[PIDConnection]


_PROMPT = (
    "This image is one page of a piping-and-instrumentation-diagram (P&ID) "
    "reference document. Perform an exhaustive drawing inventory, not a "
    "high-level summary. If this page contains an actual P&ID diagram: "
    "(1) enumerate every visible equipment item, vessel, exchanger, pump, "
    "turbine, valve, instrument bubble, transmitter, controller, indicator, "
    "and labelled line endpoint; (2) retain the exact text shown inside or "
    "beside each symbol as its tag; when the same short code occurs more than "
    "once, include every occurrence as a separate entity and disambiguate its "
    "tag with a stable '-N' suffix (for example FI-1, FI-2) while preserving "
    "the original code in label; and (3) emit every visible process, signal, "
    "electrical, pneumatic, and control connection between listed endpoints. "
    "Trace dashed as well as solid lines. Do not omit repeated instrument "
    "bubbles or a connection merely because a line crosses another line. "
    "Use a concise label and a symbol type such as pump, valve, vessel, "
    "controller, indicator, transmitter, or line_endpoint. Include a "
    "one-sentence summary. If the page is plain text/prose with no diagram, "
    "return empty entities and connections lists and an empty page_summary."
)

_CONNECTION_AUDIT_PROMPT = (
    "Inspect this P&ID image only for connectivity. Trace every distinct "
    "solid process line, dashed control/signal line, electrical/pneumatic "
    "line, and branch between labelled equipment or instrument symbols. "
    "Return one connection per directly linked pair and include repeated "
    "instrument bubbles. Do not collapse a controller loop into a single "
    "relationship: preserve its sensor-to-controller and controller-to-final-"
    "element links. Use the exact visible tag wherever possible; add an "
    "occurrence suffix only when two identical labels must be distinguished. "
    "Do not invent a link where the drawing provides no line."
)


def _extract_page(image, client) -> PIDExtraction:
    response = throttled_generate(
        client,
        model=GEMINI_MODEL,
        contents=[_PROMPT, image],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PIDExtraction,
        ),
    )
    return PIDExtraction.model_validate_json(response.text)


def _audit_connections(image, client) -> list[PIDConnection]:
    response = throttled_generate(
        client,
        model=GEMINI_MODEL,
        contents=[_CONNECTION_AUDIT_PROMPT, image],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PIDConnectionAudit,
        ),
    )
    return PIDConnectionAudit.model_validate_json(response.text).connections


def _merge_connections(*groups: list[PIDConnection]) -> list[PIDConnection]:
    """Keep one representation for each directed, typed visual relationship."""
    seen: set[tuple[str, str, str]] = set()
    merged: list[PIDConnection] = []
    for group in groups:
        for connection in group:
            key = (
                connection.from_tag.strip().lower(),
                connection.to_tag.strip().lower(),
                connection.line_type.strip().lower(),
            )
            if key not in seen:
                seen.add(key)
                merged.append(connection)
    return merged


def extract(
    pdf_path: Path, gemini_client, pages: list[int] | None = None,
) -> list[PIDPage]:
    """Return structured results for pages containing diagram content.

    `pages`: 1-indexed page numbers to process; None = every page (the
    correct default for real ingestion). Callers on a tight API quota can
    pass a short list to validate against a known-diagram subset instead of
    burning quota on every page — see cli_test.py / vision_pnid.py __main__.
    """
    import pdfplumber

    results = []
    with pdfplumber.open(pdf_path) as pdf:
        page_indices = pages if pages is not None else range(1, len(pdf.pages) + 1)
        for i in page_indices:
            page = pdf.pages[i - 1]
            # Engineering labels and dashed control lines are frequently too
            # small at the old 150dpi rasterization.  250dpi preserves them
            # without making a single-page Gemini request impractically large.
            img = page.to_image(resolution=250).original
            extraction = _extract_page(img, gemini_client)
            audited_connections = _audit_connections(img, gemini_client)
            connections = _merge_connections(
                extraction.connections,
                audited_connections,
            )
            if extraction.entities or connections:
                results.append(PIDPage(
                    page_ref=str(i),
                    page_summary=extraction.page_summary,
                    entities=extraction.entities,
                    connections=connections,
                ))
                print(f"   page {i}: {len(extraction.entities)} entities, "
                      f"{len(connections)} connections", flush=True)
    return results


if __name__ == "__main__":
    # ponytail: validates against 2 known-diagram pages, not all 42 — Gemini
    # free-tier daily quota (20 RPD) makes a full scan impractical for a
    # manual dev check; pipeline.ingest_file() still defaults to every page.
    import os
    import sys

    import truststore
    truststore.inject_into_ssl()
    from dotenv import load_dotenv
    from google import genai

    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(repo_root / ".env")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    pdf_path = repo_root / "data" / "pnid" / "sample_pnid.pdf"
    # page 3 = Figure 1 (simple pump+valve P&ID), page 21 = Figure 15
    # (cryogenic O2 generation P&ID) — both confirmed via pdfplumber text
    # search to contain real diagrams, at zero Gemini-quota cost.
    results = extract(pdf_path, client, pages=[3, 21])

    print(f"\n{len(results)} page(s) with detected diagrams:")
    for page in results:
        tags = [e.tag for e in page.entities]
        print(f"  page {page.page_ref}: {page.page_summary!r}")
        print(f"    tags: {tags}")
        print(f"    connections: {len(page.connections)}")
