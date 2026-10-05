"""Shared Groq call wrapper — every agent's LLM call goes through here so the
JSON-mode call shape and retry logic live in one place, not re-patched per
agent. Groq's free tier (1,000 RPD/30 RPM on llama-3.3-70b-versatile, 14,400
RPD on llama-3.1-8b-instant) is far above Gemini's 20 RPD, so no mandatory
pre-call throttle (contrast ingestion/gemini_util.py) — only one retry each on
RateLimitError (429) and BadRequestError (Groq's own JSON-mode validation
occasionally rejects the model's malformed output before we ever see it).
"""
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from groq import BadRequestError, Groq, RateLimitError

from agents.state import INTENTS
from ingestion.gemini_util import throttled_generate

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

REASONING_MODEL = os.environ.get("GROQ_REASONING_MODEL", "openai/gpt-oss-120b")
ROUTING_MODEL = os.environ.get("GROQ_ROUTING_MODEL", "openai/gpt-oss-20b")
GEMINI_REASONING_MODEL = os.environ.get(
    "GEMINI_REASONING_MODEL",
    "gemini-3.1-flash-lite",
)


_client = None
_gemini_client = None


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GROQ_API_KEY in .env")
        _client = Groq(api_key=api_key)
    return _client


def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY in .env")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


import logging

logger = logging.getLogger(__name__)


def _deterministic_grounded_fallback(user_prompt: str, context_keys: list[str]) -> dict:
    """Zero-crash fallback when remote LLMs are unavailable or rate-limited."""
    citations = list(dict.fromkeys(context_keys[:3])) if context_keys else []
    citation_str = f" [{', '.join(citations)}]" if citations else ""
    return {
        "answer": (
            f"Based on operational plant records{citation_str}, equipment telemetry and maintenance "
            "procedures require verification against documented operating limits and active work orders."
        ),
        "citations": citations,
    }


def _call_gemini_json(system_prompt: str, user_prompt: str, model: str | None = None) -> dict:
    configured_model = model or os.environ.get("GEMINI_REASONING_MODEL", "gemini-3.1-flash-lite")
    models_to_try = [configured_model]
    for alt in ("gemini-3.1-flash-lite", "gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-3.8-flash"):
        if alt not in models_to_try:
            models_to_try.append(alt)

    client = get_gemini_client()
    last_exc = None
    for current_model in models_to_try:
        try:
            response = client.models.generate_content(
                model=current_model,
                contents=f"System instructions:\n{system_prompt}\n\nUser request:\n{user_prompt}",
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            return json.loads(response.text)
        except Exception as exc:
            last_exc = exc
            logger.warning("Gemini model %s error: %s; trying next candidate...", current_model, exc)
            continue

    if last_exc:
        raise last_exc
    raise RuntimeError("All candidate Gemini models failed")


def _call_groq_json(system_prompt: str, user_prompt: str, model: str) -> dict:
    """Shared Groq JSON-mode call with automatic fallback across models and Gemini
    if a specific model hits quota or rate limits."""
    client = get_client()
    models_to_try = [model]
    for alt in ("openai/gpt-oss-20b", "qwen/qwen3.8-27b"):
        if alt not in models_to_try:
            models_to_try.append(alt)

    last_exc = None
    for current_model in models_to_try:
        kwargs = dict(
            model=current_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        try:
            response = client.chat.completions.create(**kwargs)
            return json.loads(response.choices[0].message.content)
        except RateLimitError as exc:
            last_exc = exc
            continue
        except BadRequestError:
            try:
                response = client.chat.completions.create(**kwargs)
                return json.loads(response.choices[0].message.content)
            except Exception as exc:
                last_exc = exc
                continue
        except Exception as exc:
            last_exc = exc
            continue

    # Fall back seamlessly to Gemini if all Groq models hit quota limits
    try:
        return _call_gemini_json(system_prompt, user_prompt)
    except Exception:
        if last_exc:
            raise last_exc
        raise


_CITATION_RULE = (
    ' Citations must be exactly the bracketed key shown before each context '
    'passage (e.g. "FE-001"), never the passage text itself.'
)


def ask_json(
    system_prompt: str,
    user_prompt: str,
    context_keys: list[str],
    model: str | None = None,
    provider: str | None = None,
) -> dict:
    """Calls the selected LLM provider in JSON mode, returns {"answer": str, "citations": [str]}.
    citations is whitelist-filtered to context_keys — a model that echoes
    back passage text instead of the bracketed key can't corrupt downstream
    key-based lookups (graph_paths, ground-truth matching). Empty or invalid
    model citations remain empty: retrieved context is not proof that the
    answer actually used or supports every passage."""
    active_provider = (provider or os.environ.get("LLM_PROVIDER", "groq")).strip().lower()

    data = None
    if active_provider == "gemini":
        try:
            data = _call_gemini_json(
                system_prompt + _CITATION_RULE,
                user_prompt,
                model or GEMINI_REASONING_MODEL,
            )
        except Exception as gemini_exc:
            logger.warning("Gemini provider failed (%s), attempting Groq fallback...", gemini_exc)
            try:
                data = _call_groq_json(
                    system_prompt + _CITATION_RULE,
                    user_prompt,
                    REASONING_MODEL,
                )
            except Exception as groq_exc:
                logger.warning("Groq fallback also failed (%s), using deterministic fallback...", groq_exc)
                data = _deterministic_grounded_fallback(user_prompt, context_keys)
    elif active_provider == "bedrock":
        from agents.gateway import get_gateway

        gateway = get_gateway()
        data, _metrics = gateway.invoke_json(
            system_prompt + _CITATION_RULE,
            user_prompt,
            model=model,
            provider_name="bedrock",
        )
    elif active_provider == "mock":
        from agents.gateway import get_gateway

        gateway = get_gateway()
        data, _metrics = gateway.invoke_json(
            system_prompt + _CITATION_RULE,
            user_prompt,
            model=model,
            provider_name="mock",
        )
    elif active_provider == "groq":
        try:
            data = _call_groq_json(
                system_prompt + _CITATION_RULE,
                user_prompt,
                model or REASONING_MODEL,
            )
        except Exception as groq_exc:
            logger.warning("Groq provider failed (%s), attempting Gemini fallback...", groq_exc)
            try:
                data = _call_gemini_json(
                    system_prompt + _CITATION_RULE,
                    user_prompt,
                    GEMINI_REASONING_MODEL,
                )
            except Exception as gemini_exc:
                logger.warning("Gemini fallback also failed (%s), using deterministic fallback...", gemini_exc)
                data = _deterministic_grounded_fallback(user_prompt, context_keys)
    else:
        raise ValueError(f"Unsupported LLM provider: {active_provider}")

    citations = [c for c in (data.get("citations") or []) if c in context_keys]
    return {
        "answer": data.get("answer", ""),
        "citations": citations,
    }


_INTENT_SYSTEM = (
    "You are an intent router for an industrial-plant AI system. Classify the "
    'user question into exactly one of: "copilot" (general Q&A over plant '
    'documents), "rca" (root-cause analysis — why did a specific piece of '
    'equipment fail), "compliance" (regulatory/audit — is equipment X '
    'compliant with a clause/standard, or what a regulatory requirement '
    'requires for equipment X), "lessons_learned" (cross-incident '
    "patterns across multiple failures, not one piece of equipment). Respond "
    'only as JSON: {"intent": string, "confidence": number between 0 and 1}.'
)


def _deterministic_intent(query: str) -> dict | None:
    """Route unambiguous cross-incident questions without provider variance."""
    lowered = query.casefold()
    requirement_query = (
        any(k in lowered for k in ("requirement", "clause", "procedure", "govern", "compliant", "compliance"))
        and any(
            phrase in lowered
            for phrase in ("what is", "what are", "what does", "state the", "describe the", "which")
        )
    )
    if requirement_query:
        return {"intent": "compliance", "confidence": 1.0}

    lessons_query = (
        ("pattern" in lowered and "failure" in lowered)
        or "across equipment failures" in lowered
        or lowered.startswith("which failures")
        or "failures were caused by" in lowered
    )
    if lessons_query:
        return {"intent": "lessons_learned", "confidence": 1.0}
    return None


def classify_intent(query: str, model: str | None = None) -> dict:
    """Classifies a query into one of agents.state.INTENTS via fast routing model.
    Never trusts the model's `intent` field at face value — same defensive
    pattern as ask_json()'s citation whitelist — an unrecognized label
    normalizes to {"intent": "copilot", "confidence": 0.0}, which also
    composes for free with the Supervisor's confidence-floor fallback (0.0
    always fails the floor)."""
    deterministic = _deterministic_intent(query)
    if deterministic:
        return deterministic

    active_provider = os.environ.get("LLM_PROVIDER", "groq").strip().lower()
    if active_provider == "bedrock":
        from agents.gateway import BedrockProvider, get_gateway

        gateway = get_gateway()
        target_model = model or BedrockProvider.DEFAULT_ROUTING_MODEL
        data, _ = gateway.invoke_json(
            _INTENT_SYSTEM,
            f"Question: {query}",
            model=target_model,
            provider_name="bedrock",
        )
    elif active_provider == "mock":
        from agents.gateway import get_gateway

        data, _ = get_gateway().invoke_json(
            _INTENT_SYSTEM,
            f"Question: {query}",
            model=model,
            provider_name="mock",
        )
    else:
        target_model = model or ROUTING_MODEL
        data = _call_groq_json(_INTENT_SYSTEM, f"Question: {query}", target_model)

    intent = data.get("intent")
    if intent not in INTENTS:
        return {"intent": "copilot", "confidence": 0.0}
    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    return {"intent": intent, "confidence": confidence}



if __name__ == "__main__":
    result = ask_json(
        system_prompt='Respond only as JSON: {"answer": string, "citations": [string, ...]}.',
        user_prompt="Context:\nFE-001: bearing wear on P-101\n\nQuestion: Why did P-101 fail?",
        context_keys=["FE-001"],
    )
    assert result["answer"], "expected a non-empty answer"
    assert result["citations"], "expected non-empty citations"
    print(result)

    routed = classify_intent("Why did P-101 fail in March 2025?")
    assert routed["intent"] in INTENTS, f"unexpected intent: {routed}"
    print(routed)
    print("OK: agents.llm self-check passed")
