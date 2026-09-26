"""Automated tests for sentence-level claim grounding and deep-link resolution."""
from agents.citation_resolver import resolve_sentence_citations


def test_resolve_sentence_citations_grounded():
    answer = (
        "Feed pump P-101 tripped due to high vibration on drive-end bearing. "
        "The operator observed suction valve was throttled before startup."
    )
    context = [
        ("FE-001", "Incident report: Feed pump P-101 tripped on high vibration drive-end bearing after 4 hours."),
        ("SOP-101", "Standard operating procedure: Ensure suction valve is fully open before startup."),
    ]

    result = resolve_sentence_citations(answer, context, site_id="plant-mumbai-01")

    assert result.is_sufficient_evidence is True
    assert result.grounding_status == "GROUNDED"
    assert len(result.claims) >= 2

    # Verify claim 1 binds to FE-001
    claim_1 = result.claims[0]
    assert claim_1.citation_key == "FE-001"
    assert "/documents/FE-001?site_id=plant-mumbai-01" in claim_1.deep_link
    assert claim_1.confidence > 0.50

    # Verify claim 2 binds to SOP-101
    claim_2 = result.claims[1]
    assert claim_2.citation_key == "SOP-101"
    assert "/documents/SOP-101?site_id=plant-mumbai-01" in claim_2.deep_link


def test_resolve_sentence_citations_insufficient_evidence():
    answer = "The reactor cooling jacket was replaced with carbon fiber composite in 2021."
    # Context does not mention carbon fiber or cooling jacket replacement
    context = [
        ("FE-001", "Boiler feed pump P-101 bearing temperature was 82C."),
    ]

    result = resolve_sentence_citations(answer, context, confidence_floor=0.70)
    assert result.is_sufficient_evidence is False
    assert result.grounding_status == "INSUFFICIENT_EVIDENCE"


def test_resolve_empty_context():
    answer = "Some ungrounded speculative statement."
    result = resolve_sentence_citations(answer, context_items=[])
    assert result.is_sufficient_evidence is False
    assert result.grounding_status == "INSUFFICIENT_EVIDENCE"
    assert len(result.claims) == 0
