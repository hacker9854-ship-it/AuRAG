"""Automated tests for ISA-5.1 tag normalizer, document supersession, and quarantine scanner."""
from ingestion.quarantine import scan_file_bytes
from ingestion.supersession import SupersessionManager, parse_document_revision
from ingestion.tag_normalizer import extract_canonical_tags, normalize_equipment_tag


def test_isa_5_1_tag_normalization_variants():
    # Standard pump variations
    assert normalize_equipment_tag("P101") == "P-101"
    assert normalize_equipment_tag("P-101") == "P-101"
    assert normalize_equipment_tag("p_101") == "P-101"
    assert normalize_equipment_tag("PUMP 101") == "P-101"
    assert normalize_equipment_tag("101-PUMP") == "P-101"

    # Train / sub-train designations
    assert normalize_equipment_tag("P-101-A") == "P-101A"
    assert normalize_equipment_tag("P_101_B") == "P-101B"
    assert normalize_equipment_tag("P101A") == "P-101A"

    # Other industrial equipment classes
    assert normalize_equipment_tag("TK-0301") == "TK-301"
    assert normalize_equipment_tag("Tank 301") == "TK-301"
    assert normalize_equipment_tag("HEX-202") == "HEX-202"
    assert normalize_equipment_tag("EXCH-202") == "HEX-202"
    assert normalize_equipment_tag("CV-105") == "CV-105"
    assert normalize_equipment_tag("TI-101") == "TI-101"

    # Invalid / unrelated tokens
    assert normalize_equipment_tag("random_unrelated_word") is None
    assert normalize_equipment_tag("") is None


def test_extract_canonical_tags_from_text():
    text = (
        "During shift handover, technician noted that pump P101 exhibited high bearing "
        "temperature while running motor M-101. Inlet valve CV-105 was throttled, "
        "and discharge pressure on PI-101 dropped. Storage tank TK301 was unaffected."
    )
    tags = extract_canonical_tags(text)
    assert "P-101" in tags
    assert "M-101" in tags
    assert "CV-105" in tags
    assert "PI-101" in tags
    assert "TK-301" in tags


def test_parse_document_revision():
    rev1 = parse_document_revision("SOP-P101-Startup-Rev2.pdf")
    assert rev1.base_id == "SOP-P101-Startup"
    assert rev1.revision == 2
    assert rev1.extension == "pdf"

    rev2 = parse_document_revision("HAZOP_TK301_v3.docx")
    assert rev2.base_id == "HAZOP_TK301"
    assert rev2.revision == 3

    rev_default = parse_document_revision("Unversioned-Guide.pdf")
    assert rev_default.revision == 1


def test_supersession_manager():
    mgr = SupersessionManager()

    # Upload Rev 1
    r1 = mgr.register_document("SOP-P101-Startup-Rev1.pdf")
    assert r1["status"] == "ACTIVE"
    assert r1["revision"] == 1

    # Upload Rev 2 -> Supersedes Rev 1
    r2 = mgr.register_document("SOP-P101-Startup-Rev2.pdf")
    assert r2["status"] == "ACTIVE"
    assert r2["revision"] == 2
    assert r2["supersedes"] == "SOP-P101-Startup-Rev1.pdf"

    # Uploading older Rev 1 later -> marked as SUPERSEDED
    r_old = mgr.register_document("SOP-P101-Startup-Rev1.pdf")
    assert r_old["status"] == "SUPERSEDED"
    assert r_old["superseded_by"] == "SOP-P101-Startup-Rev2.pdf"


def test_quarantine_scanner():
    # 1. Zero byte file
    res_empty = scan_file_bytes(b"", "empty.pdf")
    assert res_empty.is_safe is False
    assert "Empty" in res_empty.quarantine_reason

    # 2. Executable extension
    res_exe = scan_file_bytes(b"malicious content", "script.bat")
    assert res_exe.is_safe is False
    assert res_exe.severity == "CRITICAL"

    # 3. Corrupted PDF without magic bytes
    res_corrupt_pdf = scan_file_bytes(b"not a real pdf content", "drawing.pdf")
    assert res_corrupt_pdf.is_safe is False
    assert "magic bytes" in res_corrupt_pdf.quarantine_reason

    # 4. Valid PDF with %PDF- header
    valid_pdf_bytes = b"%PDF-1.4 sample plant schematic drawing"
    res_valid = scan_file_bytes(valid_pdf_bytes, "drawing.pdf")
    assert res_valid.is_safe is True
    assert res_valid.quarantine_reason is None
