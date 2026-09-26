"""Unit tests for the Enterprise Model Gateway, AWS Bedrock integration, and fallback routing."""
import io
import json
from unittest.mock import MagicMock
import pytest

from agents.gateway import (
    BedrockProvider,
    LLMGateway,
    MockLLMProvider,
    ModelMetrics,
    calculate_cost,
    extract_json_from_text,
    get_gateway,
)
from agents import llm


def test_calculate_cost_accuracy():
    # Claude 3.5 Sonnet: $3.00/1M in, $15.00/1M out
    model = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    cost = calculate_cost(model, input_tokens=1000, output_tokens=500)
    expected = (1000 / 1_000_000 * 3.00) + (500 / 1_000_000 * 15.00)
    assert abs(cost - expected) < 1e-5


def test_extract_json_from_text_variants():
    # 1. Plain clean JSON
    plain = '{"status": "ok", "count": 5}'
    assert extract_json_from_text(plain) == {"status": "ok", "count": 5}

    # 2. Markdown code fence
    fenced = """Here is the response:
```json
{
  "answer": "Pump P-101 tripped on thermal overload.",
  "citations": ["FE-001"]
}
```
Hope this helps!"""
    data = extract_json_from_text(fenced)
    assert data["answer"] == "Pump P-101 tripped on thermal overload."
    assert data["citations"] == ["FE-001"]

    # 3. Outer curly braces in conversational response
    conversational = "Based on the logs: { \"tripped\": true }."
    assert extract_json_from_text(conversational) == {"tripped": True}

    # 4. Invalid text raises ValueError
    with pytest.raises(ValueError):
        extract_json_from_text("No json here whatsoever.")


def test_mock_llm_provider_and_metrics():
    mock_prov = MockLLMProvider(
        response_generator=lambda sys, usr: {"answer": "Safe answer", "citations": ["FE-002"]}
    )
    result, metrics = mock_prov.invoke_json("System prompt", "User prompt")

    assert result["answer"] == "Safe answer"
    assert result["citations"] == ["FE-002"]
    assert metrics.provider == "mock"
    assert metrics.input_tokens > 0
    assert len(mock_prov.calls) == 1


def test_gateway_fallback_on_primary_failure():
    gateway = LLMGateway()

    failing_provider = MagicMock()
    failing_provider.invoke_json.side_effect = RuntimeError("Bedrock RateLimit or Network Timeout")
    gateway.register_provider("primary_failing", failing_provider)

    backup_provider = MockLLMProvider(
        response_generator=lambda sys, usr: {"answer": "Backup response", "citations": []}
    )
    gateway.register_provider("backup_mock", backup_provider)

    # Test automatic fallback from failing primary to backup
    result, metrics = gateway.invoke_json(
        "System prompt",
        "User prompt",
        provider_name="primary_failing",
        fallback_provider="backup_mock",
    )

    assert result["answer"] == "Backup response"
    assert metrics.provider == "mock"
    telemetry = gateway.get_aggregated_metrics()
    assert telemetry["total_calls"] == 1


def test_bedrock_provider_invocation_with_mock_client():
    mock_boto_client = MagicMock()
    response_body = {
        "content": [
            {
                "type": "text",
                "text": '{"answer": "Root cause is cavitation due to suction valve throttling.", "citations": ["FE-001"]}',
            }
        ],
        "usage": {
            "input_tokens": 420,
            "output_tokens": 85,
        },
    }

    body_bytes = json.dumps(response_body).encode("utf-8")
    mock_boto_client.invoke_model.return_value = {"body": io.BytesIO(body_bytes)}

    bedrock = BedrockProvider(region_name="ap-south-1", client=mock_boto_client)
    result, metrics = bedrock.invoke_json(
        system_prompt="You are an industrial reliability expert.",
        user_prompt="Why did P-101 fail?",
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    )

    assert "cavitation" in result["answer"]
    assert result["citations"] == ["FE-001"]
    assert metrics.input_tokens == 420
    assert metrics.output_tokens == 85
    assert metrics.cost_usd > 0.0

    # Verify boto3 call parameters
    mock_boto_client.invoke_model.assert_called_once()
    call_kwargs = mock_boto_client.invoke_model.call_args.kwargs
    assert call_kwargs["modelId"] == "anthropic.claude-3-5-sonnet-20241022-v2:0"
    payload = json.loads(call_kwargs["body"])
    assert payload["anthropic_version"] == "bedrock-2023-05-31"
    assert payload["temperature"] == 0.0


def test_ask_json_with_mock_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    # Configure mock provider in gateway
    gw = get_gateway()
    mock_prov = MockLLMProvider(
        response_generator=lambda sys, usr: {"answer": "Overheating detected", "citations": ["FE-001", "EXTRA"]}
    )
    gw.register_provider("mock", mock_prov)

    result = llm.ask_json(
        system_prompt="Analyze pump",
        user_prompt="Explain failure",
        context_keys=["FE-001"],  # Whitelist should drop EXTRA
        provider="mock",
    )

    assert result["answer"] == "Overheating detected"
    assert result["citations"] == ["FE-001"]


def test_classify_intent_with_mock_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    gw = get_gateway()
    mock_prov = MockLLMProvider(
        response_generator=lambda sys, usr: {"intent": "rca", "confidence": 0.95}
    )
    gw.register_provider("mock", mock_prov)

    routed = llm.classify_intent("Tell me about this pump breakdown")
    assert routed["intent"] == "rca"
    assert routed["confidence"] == 0.95
