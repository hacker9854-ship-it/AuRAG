import sys
import types

google = types.ModuleType("google")
google_genai = types.ModuleType("google.genai")
google_genai.types = types.SimpleNamespace(GenerateContentConfig=lambda **kwargs: kwargs)
sys.modules.setdefault("google", google)
sys.modules.setdefault("google.genai", google_genai)
truststore = types.ModuleType("truststore")
truststore.inject_into_ssl = lambda: None
sys.modules.setdefault("truststore", truststore)

class TesseractNotFoundError(Exception):
    pass

fake_pytesseract = types.ModuleType("pytesseract")
fake_pytesseract.TesseractNotFoundError = TesseractNotFoundError
fake_pytesseract.pytesseract = types.SimpleNamespace(tesseract_cmd="")
fake_pytesseract.Output = types.SimpleNamespace(DICT="dict")
sys.modules.setdefault("pytesseract", fake_pytesseract)

fake_pil = types.ModuleType("PIL")
fake_image = types.ModuleType("PIL.Image")
fake_image.open = lambda path: object()
fake_pil.Image = fake_image
sys.modules.setdefault("PIL", fake_pil)
sys.modules.setdefault("PIL.Image", fake_image)

from pathlib import Path

from ingestion.parsers import ocr


def test_missing_tesseract_falls_back_to_gemini_and_reports_engine(monkeypatch):
    def missing(*args, **kwargs):
        raise ocr.pytesseract.TesseractNotFoundError()

    monkeypatch.setattr(ocr, "_tesseract_pass", missing)
    monkeypatch.setattr(ocr, "_gemini_vision_transcribe", lambda path, client: "P-101 note")
    monkeypatch.setenv("CLOUD_OCR_PROVIDER", "gemini")

    result = ocr.transcribe(Path("scan.png"), object())

    text, used_fallback = result
    assert (text, used_fallback) == ("P-101 note", True)
    assert result.engine == "gemini"
    assert result.used_cloud_fallback is True


def test_missing_tesseract_prefers_configured_google_vision(monkeypatch):
    monkeypatch.setattr(
        ocr,
        "_tesseract_pass",
        lambda path: ("", 0.0),
    )
    monkeypatch.setattr(
        ocr,
        "_google_vision_transcribe",
        lambda path, api_key: "P-101 handwritten note",
    )
    monkeypatch.setenv("CLOUD_OCR_PROVIDER", "google_vision")
    monkeypatch.setenv("GOOGLE_VISION_API_KEY", "test-key")

    result = ocr.transcribe(Path("scan.png"))

    assert tuple(result) == ("P-101 handwritten note", True)
    assert result.engine == "google_vision"
    assert result.used_gemini_fallback is False


def test_google_vision_request_uses_document_text_detection(tmp_path):
    image_path = tmp_path / "scan.png"
    image_path.write_bytes(b"image-bytes")
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "responses": [
                    {"fullTextAnnotation": {"text": "Detected text\n"}}
                ]
            }

    def post(url, **kwargs):
        captured.update({"url": url, **kwargs})
        return Response()

    text = ocr._google_vision_transcribe(
        image_path,
        "test-key",
        post=post,
    )

    assert text == "Detected text"
    assert captured["params"] == {"key": "test-key"}
    assert captured["json"]["requests"][0]["features"] == [
        {"type": "DOCUMENT_TEXT_DETECTION"}
    ]


def test_google_vision_failure_never_echoes_the_api_key(tmp_path):
    image_path = tmp_path / "scan.png"
    image_path.write_bytes(b"image-bytes")

    class Response:
        is_error = True
        status_code = 403

        def json(self):
            return {"error": {"message": "billing is disabled"}}

    try:
        ocr._google_vision_transcribe(
            image_path,
            "secret-key",
            post=lambda *_args, **_kwargs: Response(),
        )
    except RuntimeError as exc:
        assert "billing is disabled" in str(exc)
        assert "secret-key" not in str(exc)
    else:
        raise AssertionError("expected Google Vision failure")
