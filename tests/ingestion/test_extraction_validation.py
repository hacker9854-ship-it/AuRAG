from ingestion.validate_extraction_accuracy import _missing


def test_required_extraction_terms_are_checked_case_insensitively():
    assert _missing(["P-101", "R. Sharma"], {"p-101", "R. Sharma"}) == []
    assert _missing(["P-101", "R. Sharma"], {"P-101"}) == ["R. Sharma"]
