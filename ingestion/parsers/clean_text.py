"""Path 1: clean digital documents — no OCR/vision needed.

- Markdown: split on '## ' headers (one chunk per section; incident_log.md's
  sections are one-per-FailureEvent, which is the right retrieval granularity).
- Generic PDF: pdfplumber per page, further split on blank-line paragraph
  breaks if a page is long.
"""
import re
from pathlib import Path
from typing import Literal

import pdfplumber

MAX_PAGE_CHARS = 1500

_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_H2_SPLIT_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def parse_markdown(path: Path) -> list[tuple[str, str]]:
    """Return [(page_ref, text), ...], one entry per '## ' section, plus a
    leading entry for any preamble before the first '## ' (title/metadata)."""
    raw = path.read_text(encoding="utf-8")
    h1_match = _H1_RE.search(raw)
    title = h1_match.group(1).strip() if h1_match else path.stem

    headers = list(_H2_SPLIT_RE.finditer(raw))
    chunks: list[tuple[str, str]] = []

    preamble_end = headers[0].start() if headers else len(raw)
    preamble = raw[:preamble_end].strip()
    if len(preamble) > 20:
        chunks.append((title, preamble))

    for i, m in enumerate(headers):
        section_start = m.end()
        section_end = headers[i + 1].start() if i + 1 < len(headers) else len(raw)
        body = raw[section_start:section_end].strip()
        page_ref = m.group(1).strip()
        if body:
            chunks.append((page_ref, f"{page_ref}\n\n{body}"))

    return chunks


def parse_pdf(path: Path) -> list[tuple[str, str]]:
    """Return [(page_ref, text), ...] — one entry per PDF page, further split
    on blank-line paragraph breaks if a page exceeds MAX_PAGE_CHARS."""
    chunks: list[tuple[str, str]] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            if len(text) <= MAX_PAGE_CHARS:
                chunks.append((str(i), text))
                continue
            for j, para in enumerate(re.split(r"\n\s*\n+", text), start=1):
                para = para.strip()
                if para:
                    chunks.append((f"{i}.{j}", para))
    return chunks


def classify_pdf(path: Path) -> Literal["text", "vision"]:
    """Text-bearing PDF -> 'text' (this parser); text-less (scanned/diagram)
    PDF -> 'vision' (P&ID path handles both diagrams and text-less scans for
    Phase 2 — see NOTES.md scope boundary)."""
    with pdfplumber.open(path) as pdf:
        sample = "".join((p.extract_text() or "") for p in pdf.pages[:3])
    return "text" if len(sample.strip()) > 200 else "vision"


def parse_clean_text(path: Path) -> list[tuple[str, str]]:
    """Dispatch by extension: .md/.txt -> parse_markdown, .pdf -> parse_pdf."""
    suffix = path.suffix.lower()
    if suffix in (".md", ".txt"):
        return parse_markdown(path)
    if suffix == ".pdf":
        return parse_pdf(path)
    raise ValueError(f"parse_clean_text: unsupported extension {suffix!r} for {path}")


if __name__ == "__main__":
    # ponytail: one runnable check — real docs, not fixtures
    repo_root = Path(__file__).resolve().parents[2]
    sop = parse_markdown(repo_root / "data" / "documents" / "pump_pm_sop.md")
    log = parse_markdown(repo_root / "data" / "documents" / "incident_log.md")

    assert len(sop) == 7, f"expected 7 chunks (preamble + 6 '##' sections) in SOP, got {len(sop)}"
    assert any("P-101" in t for _, t in sop), "SOP should mention P-101 somewhere"

    assert len(log) == 7, f"expected 7 chunks (preamble + 6 FailureEvents) in incident log, got {len(log)}"
    fe_refs = [ref for ref, _ in log if ref.startswith("FE-")]
    assert [r[:6] for r in fe_refs] == [f"FE-00{i}" for i in range(1, 7)], f"unexpected FE ordering: {fe_refs}"
    assert any("WO-1002" in t for ref, t in log if ref.startswith("FE-001")), "FE-001 chunk should mention WO-1002"

    print(f"OK: SOP -> {len(sop)} chunks, incident log -> {len(log)} chunks")
    for ref, text in log:
        print(f"  [{ref}] {len(text)} chars")
