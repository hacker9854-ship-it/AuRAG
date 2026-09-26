"""Provider-backed OCR and P&ID extraction acceptance thresholds.

This validator intentionally checks raw extraction before closed-world graph
matching. It exits non-zero on missed manually reviewed evidence.
"""

import json
from pathlib import Path

from ingestion.parsers.ocr import transcribe
from ingestion.parsers.vision_pnid import extract as extract_pid
from ingestion.pipeline import extract_entities_llm, get_gemini_client

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_FILE = REPO_ROOT / "ingestion" / "extraction_baseline.json"


def _missing(required: list[str], actual: set[str]) -> list[str]:
    lowered = {item.lower() for item in actual}
    return [item for item in required if item.lower() not in lowered]


def main() -> None:
    baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    client = get_gemini_client()
    failures: list[str] = []

    ocr_config = baseline["ocr"]
    ocr_result = transcribe(REPO_ROOT / ocr_config["file"], client)
    text = ocr_result.text
    for term in ocr_config["required_text_terms"]:
        if term.lower() not in text.lower():
            failures.append(f"OCR text missed required term: {term}")
    mentions = {
        mention.raw_text
        for mention in extract_entities_llm(client, text)
    }
    missing_mentions = _missing(ocr_config["required_mentions"], mentions)
    failures.extend(
        f"OCR entity extraction missed required mention: {mention}"
        for mention in missing_mentions
    )
    print(
        f"OCR engine={ocr_result.engine}; "
        f"{len(mentions)} raw mention(s); "
        f"{len(missing_mentions)} required mention(s) missed"
    )

    pid_config = baseline["pid"]
    pages = extract_pid(
        REPO_ROOT / pid_config["file"],
        client,
        pages=pid_config["pages"],
    )
    tags = {
        entity.tag
        for page in pages
        for entity in page.entities
    }
    connection_count = sum(len(page.connections) for page in pages)
    if len(tags) < pid_config["minimum_entities"]:
        failures.append(
            f"P&ID extracted {len(tags)} unique entities; "
            f"minimum is {pid_config['minimum_entities']}"
        )
    if connection_count < pid_config["minimum_connections"]:
        failures.append(
            f"P&ID extracted {connection_count} connections; "
            f"minimum is {pid_config['minimum_connections']}"
        )
    if not any(tag.lower() in {value.lower() for value in tags} for tag in pid_config["required_any_tags"]):
        failures.append(
            "P&ID extraction missed every manually reviewed anchor tag: "
            + ", ".join(pid_config["required_any_tags"])
        )
    print(
        f"P&ID pages={pid_config['pages']}; "
        f"{len(tags)} unique entities; {connection_count} connections"
    )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(
            f"Extraction accuracy validation failed with {len(failures)} issue(s)."
        )
    print("OK: OCR and P&ID extraction thresholds passed")


if __name__ == "__main__":
    main()
