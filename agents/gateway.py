"""Enterprise Model Gateway for AuRAG.

Provides a unified, resilient inference gateway supporting Amazon Bedrock
(Claude 3.5 Sonnet / Haiku), Groq, Google Gemini, and deterministic Mock providers.

Key Enterprise Capabilities:
- Zero Data Retention: Bedrock guarantees customer prompts are never stored or used
  for foundation model training.
- VPC PrivateLink: Bedrock traffic stays within the AWS Mumbai private boundary.
- Telemetry & Cost Accounting: Tracks input/output token counts, latency, and estimated
  costs across every agent reasoning call.
- Automated Failover: Handles transient provider rate limits and throttles with
  exponential backoff and fallback routing.
"""
import json
import os
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ModelMetrics:
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0


# Estimated pricing per 1M tokens (USD)
PRICING_MAP = {
    # Anthropic on AWS Bedrock
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": 3.00, "output": 15.00},
    "anthropic.claude-3-5-sonnet-20240620-v1:0": {"input": 3.00, "output": 15.00},
    "anthropic.claude-3-5-haiku-20241022-v1:0": {"input": 0.80, "output": 4.00},
    "anthropic.claude-3-haiku-20240307-v1:0": {"input": 0.25, "output": 1.25},
    # Groq / Open Models
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    # Gemini
    "gemini-3.1-flash-lite": {"input": 0.075, "output": 0.30},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rate = PRICING_MAP.get(model, {"input": 1.0, "output": 3.0})
    input_cost = (input_tokens / 1_000_000.0) * rate["input"]
    output_cost = (output_tokens / 1_000_000.0) * rate["output"]
    return round(input_cost + output_cost, 6)


def extract_json_from_text(text: str) -> dict:
    """Safely extract a JSON object from text, handling markdown blocks or extra wrapper strings."""
    stripped = text.strip()
    # 1. Direct JSON parse
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 2. Markdown fenced code block ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Find outermost curly braces
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = stripped[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to parse valid JSON from model response: {text[:200]}...")


class LLMProvider(ABC):
    @abstractmethod
    def invoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
    ) -> tuple[dict, ModelMetrics]:
        pass


class BedrockProvider(LLMProvider):
    """AWS Bedrock Model Provider using boto3 bedrock-runtime."""

    DEFAULT_REASONING_MODEL = os.environ.get(
        "BEDROCK_REASONING_MODEL",
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
    )
    DEFAULT_ROUTING_MODEL = os.environ.get(
        "BEDROCK_ROUTING_MODEL",
        "anthropic.claude-3-5-haiku-20241022-v1:0",
    )

    def __init__(self, region_name: str | None = None, client: Any = None):
        self.region_name = region_name or os.environ.get("AWS_REGION", "ap-south-1")
        self._client = client

    def get_client(self):
        if self._client is None:
            import boto3

            self._client = boto3.client(
                service_name="bedrock-runtime",
                region_name=self.region_name,
            )
        return self._client

    def invoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
    ) -> tuple[dict, ModelMetrics]:
        target_model = model or self.DEFAULT_REASONING_MODEL
        client = self.get_client()

        # Enforce JSON-mode instruction in system prompt
        json_system = system_prompt + "\nIMPORTANT: You must respond ONLY with valid, parseable JSON."
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "temperature": 0.0,
            "system": json_system,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        start_time = time.time()
        # Retry loop for Bedrock ThrottlingException
        max_retries = 3
        backoff = 2.0
        response = None

        for attempt in range(max_retries):
            try:
                response = client.invoke_model(
                    modelId=target_model,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(payload),
                )
                break
            except Exception as exc:
                exc_str = str(exc).lower()
                is_throttle = "throttling" in exc_str or "toomanyrequests" in exc_str
                if is_throttle and attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    raise

        latency_ms = (time.time() - start_time) * 1000.0
        response_body = json.loads(response["body"].read().decode("utf-8"))

        content_blocks = response_body.get("content", [])
        text_output = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        parsed = extract_json_from_text(text_output)

        usage = response_body.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        cost = calculate_cost(target_model, input_tokens, output_tokens)

        metrics = ModelMetrics(
            provider="bedrock",
            model=target_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=round(latency_ms, 2),
            cost_usd=cost,
        )
        return parsed, metrics


class GroqProvider(LLMProvider):
    """Groq Model Provider wrapping agents.llm._call_groq_json."""

    def invoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
    ) -> tuple[dict, ModelMetrics]:
        from agents.llm import REASONING_MODEL, _call_groq_json

        target_model = model or REASONING_MODEL
        start_time = time.time()
        parsed = _call_groq_json(system_prompt, user_prompt, target_model)
        latency_ms = (time.time() - start_time) * 1000.0

        # Estimated tokens based on prompt length
        est_in = max(1, len(system_prompt + user_prompt) // 4)
        est_out = max(1, len(json.dumps(parsed)) // 4)
        cost = calculate_cost(target_model, est_in, est_out)

        metrics = ModelMetrics(
            provider="groq",
            model=target_model,
            input_tokens=est_in,
            output_tokens=est_out,
            latency_ms=round(latency_ms, 2),
            cost_usd=cost,
        )
        return parsed, metrics


class GeminiProvider(LLMProvider):
    """Google Gemini Provider wrapping agents.llm._call_gemini_json."""

    def invoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
    ) -> tuple[dict, ModelMetrics]:
        from agents.llm import GEMINI_REASONING_MODEL, _call_gemini_json

        target_model = model or GEMINI_REASONING_MODEL
        start_time = time.time()
        parsed = _call_gemini_json(system_prompt, user_prompt, target_model)
        latency_ms = (time.time() - start_time) * 1000.0

        est_in = max(1, len(system_prompt + user_prompt) // 4)
        est_out = max(1, len(json.dumps(parsed)) // 4)
        cost = calculate_cost(target_model, est_in, est_out)

        metrics = ModelMetrics(
            provider="gemini",
            model=target_model,
            input_tokens=est_in,
            output_tokens=est_out,
            latency_ms=round(latency_ms, 2),
            cost_usd=cost,
        )
        return parsed, metrics


class MockLLMProvider(LLMProvider):
    """Deterministic Mock Provider for unit testing and offline development."""

    def __init__(self, response_generator: Callable[[str, str], dict] | None = None):
        self.response_generator = response_generator
        self.calls = []

    def invoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
    ) -> tuple[dict, ModelMetrics]:
        self.calls.append({"system": system_prompt, "user": user_prompt, "model": model})
        if self.response_generator:
            data = self.response_generator(system_prompt, user_prompt)
        else:
            data = {"answer": "Mock grounded answer.", "citations": []}

        metrics = ModelMetrics(
            provider="mock",
            model=model or "mock-model",
            input_tokens=50,
            output_tokens=25,
            latency_ms=1.5,
            cost_usd=0.0,
        )
        return data, metrics


class LLMGateway:
    """Central orchestrator managing provider selection, fallbacks, and telemetry."""

    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._telemetry_history: list[ModelMetrics] = []

    def register_provider(self, name: str, provider: LLMProvider):
        self._providers[name.lower()] = provider

    def get_provider(self, name: str | None = None) -> LLMProvider:
        requested = (name or os.environ.get("LLM_PROVIDER", "auto")).strip().lower()

        if requested in self._providers:
            return self._providers[requested]

        if requested == "bedrock":
            provider = BedrockProvider()
            self._providers["bedrock"] = provider
            return provider
        elif requested == "gemini":
            provider = GeminiProvider()
            self._providers["gemini"] = provider
            return provider
        elif requested == "mock":
            provider = MockLLMProvider()
            self._providers["mock"] = provider
            return provider
        elif requested == "groq":
            provider = GroqProvider()
            self._providers["groq"] = provider
            return provider

        # Auto selection: Bedrock if AWS configured, otherwise Groq
        if os.environ.get("BEDROCK_ENABLED", "").lower() in ("true", "1", "yes") or (
            os.environ.get("AWS_ACCESS_KEY_ID") and not os.environ.get("GROQ_API_KEY")
        ):
            provider = BedrockProvider()
            self._providers["bedrock"] = provider
            return provider

        provider = GroqProvider()
        self._providers["groq"] = provider
        return provider

    def invoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        provider_name: str | None = None,
        fallback_provider: str | None = None,
    ) -> tuple[dict, ModelMetrics]:
        primary = self.get_provider(provider_name)
        try:
            result, metrics = primary.invoke_json(system_prompt, user_prompt, model=model)
            self._telemetry_history.append(metrics)
            return result, metrics
        except Exception as primary_error:
            if fallback_provider:
                secondary = self.get_provider(fallback_provider)
                result, metrics = secondary.invoke_json(system_prompt, user_prompt, model=model)
                self._telemetry_history.append(metrics)
                return result, metrics
            raise primary_error

    def get_aggregated_metrics(self) -> dict:
        total_in = sum(m.input_tokens for m in self._telemetry_history)
        total_out = sum(m.output_tokens for m in self._telemetry_history)
        total_cost = sum(m.cost_usd for m in self._telemetry_history)
        return {
            "total_calls": len(self._telemetry_history),
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "total_cost_usd": round(total_cost, 4),
            "providers_used": list({m.provider for m in self._telemetry_history}),
        }


# Global singleton gateway
_GLOBAL_GATEWAY: LLMGateway | None = None


def get_gateway() -> LLMGateway:
    global _GLOBAL_GATEWAY
    if _GLOBAL_GATEWAY is None:
        _GLOBAL_GATEWAY = LLMGateway()
    return _GLOBAL_GATEWAY
