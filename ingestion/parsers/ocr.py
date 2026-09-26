"""Path 2: scanned/handwritten documents. Local Tesseract OCR first; if mean
word confidence is low (or Tesseract found nothing), fall back to Gemini
vision on the same image — one LLM provider, no separate cloud OCR account.
"""
import base64
import os
from pathlib import Path
from typing import Literal

import httpx
import pytesseract
from google.genai import types
from PIL import Image
from pytesseract import Output

from ingestion.gemini_util import throttled_generate

CONFIDENCE_THRESHOLD = 60  # mean per-word conf (0-100); print vs. handwriting cutoff
GEMINI_MODEL = os.environ.get(
    "GEMINI_INGESTION_MODEL",
    "gemini-3.1-flash-lite",
)


class OCRResult(tuple):
    """A two-item legacy tuple with explicit OCR engine metadata."""

    def __new__(
        cls,
        text: str,
        engine: Literal["tesseract", "google_vision", "gemini"],
    ):
        result = super().__new__(cls, (text, engine != "tesseract"))
        result.engine = engine
        return result

    @property
    def text(self) -> str:
        return self[0]

    @property
    def used_gemini_fallback(self) -> bool:
        return self.engine == "gemini"

    @property
    def used_cloud_fallback(self) -> bool:
        return self[1]


def _tesseract_pass(image_path: Path) -> tuple[str, float]:
    """Returns (text, mean_conf). mean_conf is 0.0 if the tesseract binary
    isn't installed — that's treated identically to "low confidence," which
    naturally routes to the Gemini fallback rather than crashing."""
    # ponytail: read TESSERACT_CMD here, not at module import time — .env is
    # loaded by whichever entry point imports this module, which happens
    # *after* Python finishes processing this module's own top-level code,
    # so a module-level read would always see it unset.
    if os.environ.get("TESSERACT_CMD"):
        pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
    try:
        data = pytesseract.image_to_data(Image.open(image_path), output_type=Output.DICT)
    except pytesseract.TesseractNotFoundError:
        return "", 0.0
    confs = [int(c) for c in data["conf"] if c not in ("-1", -1)]
    mean_conf = sum(confs) / len(confs) if confs else 0.0
    text = " ".join(w for w in data["text"] if w.strip())
    return text, mean_conf


def _gemini_vision_transcribe(image_path: Path, client) -> str:
    image = Image.open(image_path)
    response = throttled_generate(
        client,
        model=GEMINI_MODEL,
        contents=[
            "Transcribe every word of legible text in this image verbatim, "
            "including handwritten notes, equipment tags, and dates. "
            "Return only the transcribed text, no commentary.",
            image,
        ],
        config=types.GenerateContentConfig(response_mime_type="text/plain"),
    )
    return response.text.strip()


def _google_vision_transcribe(
    image_path: Path,
    api_key: str,
    *,
    post=httpx.post,
) -> str:
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    response = post(
        "https://vision.googleapis.com/v1/images:annotate",
        params={"key": api_key},
        json={
            "requests": [
                {
                    "image": {"content": encoded},
                    "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                }
            ]
        },
        timeout=float(os.environ.get("GOOGLE_VISION_TIMEOUT_SECONDS", "60")),
    )
    payload = response.json()
    if getattr(response, "is_error", False):
        detail = (payload.get("error") or {}).get("message") or "request failed"
        raise RuntimeError(
            f"Google Vision OCR failed ({response.status_code}): {detail}"
        )
    result = (payload.get("responses") or [{}])[0]
    if result.get("error"):
        detail = result["error"].get("message") or str(result["error"])
        raise RuntimeError(f"Google Vision OCR failed: {detail}")
    text = (result.get("fullTextAnnotation") or {}).get("text")
    if not text:
        annotations = result.get("textAnnotations") or []
        text = annotations[0].get("description") if annotations else ""
    if not text or not text.strip():
        raise RuntimeError("Google Vision OCR returned no text")
    return text.strip()


def _cloud_provider() -> str:
    configured = os.environ.get("CLOUD_OCR_PROVIDER", "auto").strip().lower()
    if configured == "auto":
        return (
            "google_vision"
            if os.environ.get("GOOGLE_VISION_API_KEY")
            else "gemini"
        )
    if configured not in {"google_vision", "gemini"}:
        raise RuntimeError(
            "CLOUD_OCR_PROVIDER must be 'google_vision', 'gemini', or 'auto'"
        )
    return configured


def transcribe(image_path: Path, gemini_client=None) -> OCRResult:
    """Return legacy ``(text, fallback)`` values plus ``result.engine``."""
    try:
        text, mean_conf = _tesseract_pass(image_path)
    except pytesseract.TesseractNotFoundError:
        text, mean_conf = "", 0.0
    if mean_conf < CONFIDENCE_THRESHOLD or not text.strip():
        provider = _cloud_provider()
        if provider == "google_vision":
            api_key = os.environ.get("GOOGLE_VISION_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "GOOGLE_VISION_API_KEY is required when "
                    "CLOUD_OCR_PROVIDER=google_vision"
                )
            return OCRResult(
                _google_vision_transcribe(image_path, api_key),
                "google_vision",
            )
        if gemini_client is None:
            raise RuntimeError(
                "A Gemini client is required when CLOUD_OCR_PROVIDER=gemini"
            )
        return OCRResult(
            _gemini_vision_transcribe(image_path, gemini_client),
            "gemini",
        )
    return OCRResult(text, "tesseract")


if __name__ == "__main__":
    # ponytail: one runnable check against the real scanned sample
    import sys

    import truststore
    truststore.inject_into_ssl()
    from dotenv import load_dotenv
    from google import genai

    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(repo_root / ".env")
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key) if api_key else None
    img_path = repo_root / "data" / "scanned" / "scnd1.jpeg"

    raw_text, tess_conf = _tesseract_pass(img_path)
    print(f"Tesseract mean confidence: {tess_conf:.1f}")
    print(f"Tesseract text ({len(raw_text)} chars): {raw_text[:200]!r}")

    result = transcribe(img_path, client)
    text, used_fallback = result
    print(f"ocr_engine = {result.engine}; used_cloud_fallback = {used_fallback}")
    print(f"Final text ({len(text)} chars):\n{text}")
