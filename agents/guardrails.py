"""Industrial Safety Guardrails, PII Sanitization, and Prompt Version Registry."""
import re
from typing import NamedTuple

# Strict Safety Non-Negotiables (Bypass of safety devices, trips, relief valves)
_SAFETY_BYPASS_PATTERNS = [
    re.compile(r"\b(?:bypass|jumper|defeat|disable|override|force)\b.*\b(?:esd|trip|interlock|safety valve|psv|prv|scram)\b", re.IGNORECASE),
    re.compile(r"\b(?:how to|can i|procedure to)\b.*\b(?:silence|ignore)\b.*\b(?:gas leak|h2s|toxic|fire alarm)\b", re.IGNORECASE),
    re.compile(r"\b(?:increase|raise)\b.*\b(?:psv|prv|relief valve)\b.*\b(?:set pressure|setpoint)\b", re.IGNORECASE),
]

_SAFETY_REFUSAL_MESSAGE = (
    "SAFETY GUARDRAIL VIOLATION: AuRAG is strictly prohibited from providing guidance "
    "or instructions to bypass, jumper, or defeat Emergency Shutdown (ESD) interlocks, "
    "Pressure Safety Valves (PSVs), or toxic/fire protection systems. All protective system "
    "modifications require a signed Management of Change (MOC) under OISD-156 and OSHA 1910.119."
)

# PII Regex Patterns
_AADHAAR_PATTERN = re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b")
_PHONE_PATTERN = re.compile(r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b")
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


class GuardrailCheck(NamedTuple):
    is_safe: bool
    refusal_message: str | None


def check_safety_guardrails(query: str) -> GuardrailCheck:
    """Evaluate query against industrial safety non-negotiables."""
    if not query:
        return GuardrailCheck(is_safe=True, refusal_message=None)

    for pattern in _SAFETY_BYPASS_PATTERNS:
        if pattern.search(query):
            return GuardrailCheck(is_safe=False, refusal_message=_SAFETY_REFUSAL_MESSAGE)

    return GuardrailCheck(is_safe=True, refusal_message=None)


def mask_pii(text: str) -> str:
    """Redact sensitive personal identifiable information from queries and evidence."""
    if not text:
        return text

    masked = _AADHAAR_PATTERN.sub("[REDACTED-AADHAAR]", text)
    masked = _PHONE_PATTERN.sub("[REDACTED-PHONE]", masked)
    masked = _EMAIL_PATTERN.sub("[REDACTED-EMAIL]", masked)
    return masked


# Centralized, versioned prompt registry
PROMPT_REGISTRY = {
    "rca:v2.0": (
        "You are an industrial Root Cause Analysis (RCA) expert. Analyze the plant "
        "failure sequence step-by-step using the provided context passages. Ground each statement "
        "in an exact citation key. Never speculate beyond retrieved engineering evidence."
    ),
    "compliance:v2.0": (
        "You are an industrial safety compliance auditor. Audit the equipment against "
        "governing regulatory clauses (Factories Act, OISD, ISO). Formulate audit-ready "
        "evidence text, explicitly flag compliance gaps or overdue inspections, and cite "
        "exact clause IDs."
    ),
    "copilot:v1.5": (
        "You are an industrial plant operating assistant. Answer the operator's operational "
        "and maintenance questions accurately and concisely using retrieved plant documentation."
    ),
    "lessons_learned:v2.0": (
        "You are a plant reliability engineer synthesizing cross-incident failure patterns. "
        "Identify recurring mechanical and procedural failure modes across multiple incidents."
    ),
}


def get_prompt_template(prompt_id: str) -> str:
    """Retrieve versioned prompt text from the registry."""
    return PROMPT_REGISTRY.get(prompt_id, PROMPT_REGISTRY["copilot:v1.5"])
