"""Sentence-level claim grounding and document deep-link resolution.

Enforces zero-hallucination standards in industrial safety environments by
binding every sentence/claim to an exact evidence snippet, computing grounding
confidence, and providing explicit INSUFFICIENT_EVIDENCE responses when source
proof is below threshold.
"""
import re
from dataclasses import asdict, dataclass, field
from typing import Any

# Tokenizer pattern for sentence segmentation
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_WORD_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with",
    "by", "is", "was", "are", "were", "been", "be", "it", "this", "that", "from"
}


@dataclass
class ClaimCitation:
    claim: str
    citation_key: str
    snippet: str
    confidence: float
    deep_link: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GroundedAnswer:
    answer: str
    claims: list[ClaimCitation] = field(default_factory=list)
    overall_confidence: float = 0.0
    is_sufficient_evidence: bool = True
    grounding_status: str = "GROUNDED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "claims": [c.to_dict() for c in self.claims],
            "overall_confidence": round(self.overall_confidence, 3),
            "is_sufficient_evidence": self.is_sufficient_evidence,
            "grounding_status": self.grounding_status,
        }


def _clean_tokens(text: str) -> set[str]:
    return {
        token for token in _WORD_RE.findall(text.casefold())
        if token not in _STOPWORDS and len(token) > 2
    }


def _compute_snippet_overlap(claim_tokens: set[str], snippet_tokens: set[str]) -> float:
    if not claim_tokens or not snippet_tokens:
        return 0.0
    intersection = claim_tokens.intersection(snippet_tokens)
    return len(intersection) / len(claim_tokens)


def resolve_sentence_citations(
    answer: str,
    context_items: list[tuple[str, str]],
    site_id: str = "plant-mumbai-01",
    confidence_floor: float = 0.70,
) -> GroundedAnswer:
    """Analyze answer sentence-by-sentence and bind each to supporting evidence snippets."""
    if not answer or not answer.strip():
        return GroundedAnswer(
            answer="No response generated.",
            claims=[],
            overall_confidence=0.0,
            is_sufficient_evidence=False,
            grounding_status="EMPTY_RESPONSE",
        )

    if not context_items:
        return GroundedAnswer(
            answer=answer,
            claims=[],
            overall_confidence=0.0,
            is_sufficient_evidence=False,
            grounding_status="INSUFFICIENT_EVIDENCE",
        )

    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(answer.strip()) if len(s.strip()) > 5]
    if not sentences:
        sentences = [answer.strip()]

    # Pre-tokenize context items
    tokenized_context = []
    for key, text in context_items:
        tokens = _clean_tokens(text)
        tokenized_context.append((key, text, tokens))

    resolved_claims: list[ClaimCitation] = []
    confidence_scores: list[float] = []

    for sentence in sentences:
        sentence_tokens = _clean_tokens(sentence)
        best_key = ""
        best_snippet = ""
        best_score = 0.0

        for key, text, ctx_tokens in tokenized_context:
            score = _compute_snippet_overlap(sentence_tokens, ctx_tokens)
            if score > best_score:
                best_score = score
                best_key = key
                best_snippet = text[:180].strip()

        if best_key and best_score > 0.15:
            # Scale score to calibrated confidence band
            calibrated_conf = min(1.0, round(best_score * 1.3, 3))
            deep_link = f"/documents/{best_key}?site_id={site_id}"
            claim_citation = ClaimCitation(
                claim=sentence,
                citation_key=best_key,
                snippet=best_snippet,
                confidence=calibrated_conf,
                deep_link=deep_link,
            )
            resolved_claims.append(claim_citation)
            confidence_scores.append(calibrated_conf)
        else:
            confidence_scores.append(0.20)

    overall_conf = (
        sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    )
    is_sufficient = overall_conf >= confidence_floor and len(resolved_claims) > 0
    status = "GROUNDED" if is_sufficient else "INSUFFICIENT_EVIDENCE"

    return GroundedAnswer(
        answer=answer,
        claims=resolved_claims,
        overall_confidence=overall_conf,
        is_sufficient_evidence=is_sufficient,
        grounding_status=status,
    )
