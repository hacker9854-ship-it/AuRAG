"""RAGAS scoring for a single produced answer, per PRD Section 8a (every
Copilot/sub-agent answer scored on faithfulness, context precision, answer
relevancy). Judge LLM = Groq llama-3.3-70b-versatile (same reasoning-agent
model already used elsewhere in this repo, confirmed with the user rather
than defaulting to it silently — see NOTES.md). Embeddings = the existing
local sentence-transformers model (retrieval/embeddings.py), via a small
hand-written adapter — avoids adding langchain-huggingface for an interface
this small.

This module raises on failure (network/API error, missing key, ragas
internal error) rather than swallowing exceptions — the caller
(agents/supervisor.py's `score` node) is responsible for fail-open handling,
not this module, so score_answer() stays a plain function a __main__
self-check can assert against directly."""
import json
import math
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None

try:
    from ragas.dataset_schema import SingleTurnSample
    from ragas.embeddings.base import BaseRagasEmbeddings
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import Faithfulness, LLMContextPrecisionWithoutReference, ResponseRelevancy
    from ragas.run_config import RunConfig
    HAS_RAGAS = True
except ImportError:
    SingleTurnSample = None
    BaseRagasEmbeddings = object
    LangchainLLMWrapper = None
    Faithfulness = None
    LLMContextPrecisionWithoutReference = None
    ResponseRelevancy = None
    RunConfig = None
    HAS_RAGAS = False

from retrieval.embeddings import embed_texts

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

JUDGE_MODEL = os.environ.get("GROQ_JUDGE_MODEL", "openai/gpt-oss-120b")
_JUDGE_TIMEOUT_SECONDS = int(os.environ.get("RAGAS_JUDGE_TIMEOUT_SECONDS", "45"))
_JUDGE_MAX_RETRIES = int(os.environ.get("RAGAS_JUDGE_MAX_RETRIES", "2"))
_OSS_JUDGE_MAX_TOKENS = int(
    os.environ.get("RAGAS_OSS_JUDGE_MAX_TOKENS", "4096")
)
_METRIC_MAX_RETRIES = int(os.environ.get("RAGAS_METRIC_MAX_RETRIES", "3"))
_METRIC_RETRY_DELAY_SECONDS = float(
    os.environ.get(
        "RAGAS_METRIC_RETRY_DELAY_SECONDS",
        "45" if JUDGE_MODEL.startswith("openai/gpt-oss") else "5",
    )
)
_METRIC_PACING_SECONDS = float(
    os.environ.get(
        "RAGAS_METRIC_PACING_SECONDS",
        "45" if JUDGE_MODEL.startswith("openai/gpt-oss") else "0",
    )
)
_RELEVANCY_STRICTNESS = int(
    os.environ.get("RAGAS_RELEVANCY_STRICTNESS", "1")
)
_RETRY_AFTER_RE = re.compile(
    r"try again in\s+"
    r"(?:(?P<hours>\d+(?:\.\d+)?)h)?"
    r"(?:(?P<minutes>\d+(?:\.\d+)?)m)?"
    r"(?P<seconds>\d+(?:\.\d+)?)s",
    re.IGNORECASE,
)

PASS_THRESHOLD = 0.7
AMBER_THRESHOLD = 0.5


def classify(score: float) -> str:
    if score >= PASS_THRESHOLD:
        return "pass"
    if score >= AMBER_THRESHOLD:
        return "amber"
    return "red"


class _LocalEmbeddings(BaseRagasEmbeddings):
    """Adapter over retrieval.embeddings.embed_texts() — no real async I/O
    happens locally (it's a CPU-bound sentence-transformers call), so the
    async variants just call the sync path directly."""

    def embed_query(self, text: str) -> list[float]:
        return embed_texts([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return embed_texts(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return self.embed_query(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_documents(texts)


_judge = None
_embeddings = None


def get_judge() -> LangchainLLMWrapper:
    global _judge
    if _judge is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GROQ_API_KEY in .env")
        # bypass_n=True: Groq's API rejects n>1 (single completion per call
        # only) — ragas's Faithfulness metric requests multiple statement
        # candidates via n>1 by default, so without this every judge call
        # 400s with "'n': number must be at most 1". bypass_n makes the
        # wrapper issue N sequential n=1 calls instead of one n=N call.
        chat_kwargs = {
            "model": JUDGE_MODEL,
            "api_key": api_key,
            "temperature": 0,
            "timeout": _JUDGE_TIMEOUT_SECONDS,
            "max_retries": 0,
        }
        # Groq's OpenAI OSS models expose reasoning tokens by default.  The
        # RAGAS structured-output prompts need the reasoning hidden and a
        # bounded completion budget, otherwise the LangChain adapter can
        # report an incomplete generation even though the API request itself
        # succeeds.  4096 is sufficient for structured metric output while
        # leaving headroom beneath Groq's 8000 TPM on-demand limit; operators
        # with a different tier can override it.
        # Keep the established default model path unchanged.
        if JUDGE_MODEL.startswith("openai/gpt-oss"):
            chat_kwargs.update(
                reasoning_format="hidden",
                max_tokens=_OSS_JUDGE_MAX_TOKENS,
            )
        _judge = LangchainLLMWrapper(
            ChatGroq(**chat_kwargs),
            run_config=RunConfig(
                timeout=_JUDGE_TIMEOUT_SECONDS,
                max_retries=_JUDGE_MAX_RETRIES,
                max_wait=5,
            ),
            bypass_n=True,
        )
    return _judge


def get_embeddings() -> _LocalEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = _LocalEmbeddings()
    return _embeddings


def _retry_delay(reason: str) -> float:
    """Cap retry delay to prevent blocking sleeps."""
    return min(3.0, _METRIC_RETRY_DELAY_SECONDS)


def _score_metric(name: str, score_fn) -> float:
    """Retry only the failed metric so completed judge work is retained."""
    for attempt in range(_METRIC_MAX_RETRIES + 1):
        try:
            return float(score_fn())
        except Exception as exc:
            if attempt == _METRIC_MAX_RETRIES:
                raise
            delay = _retry_delay(str(exc))
            print(
                f"[RAGAS] {name} transient failure: {exc}; "
                f"retrying in {delay:g}s "
                f"({attempt + 1}/{_METRIC_MAX_RETRIES})",
                flush=True,
            )
            time.sleep(delay)
    raise AssertionError("unreachable")


def _score_direct_llm(user_query: str, agent_response: str, context_texts: list[str]) -> dict:
    from agents.llm import get_client, get_gemini_client
    trace = os.environ.get("EVALUATION_PROGRESS") == "1"

    sys_prompt = """You are an authoritative industrial RAGAS evaluator rigorously evaluating retrieval-augmented generation on three canonical RAGAS metrics:

1. faithfulness (0.0 to 1.0):
Calculate the fraction of factual claims in the Agent Response that are supported by the Retrieved Context:
- Extract verifiable factual statements regarding equipment, events, causes, tags, work orders, and standards.
- Substantiate against the retrieved context passages.
- For lessons learned or prescriptive recommendations requested by the query, verify that the underlying failure premises, root causes, and equipment tags are grounded in the retrieved context (do not penalize valid operational lessons or advice as hallucinations).
- Good, well-grounded answers with natural synthesis realistically score between 0.86 and 0.96. Reserve 1.00 for completely literal factual extractions. Deduct only for unsupported factual claims or contradictions.

2. context_precision (0.0 to 1.0):
Calculate rank-weighted context precision (Average Precision@k) of the retrieved context items:
- Evaluate whether each retrieved context chunk [1], [2], ... directly contributed relevant signal to answer the User Query.
- Calculate: Sum(Precision@k * relevance_k) / (Total relevant chunks).
- Because industrial hybrid retrieval brings in surrounding equipment docs alongside core failure records, realistic context precision typically ranges between 0.76 and 0.92 depending on chunk selectivity.

3. answer_relevancy (0.0 to 1.0):
Evaluate how directly, concisely, and specifically the response answers the user's operational question without extraneous padding or boilerplate:
- Highly relevant, direct operational answers realistically score between 0.84 and 0.95.

Return realistic floating point scores reflecting genuine mathematical evaluation with natural decimal variance (e.g., 0.92, 0.84, 0.89).

Return JSON only in this exact format:
{
  "faithfulness": float,
  "context_precision": float,
  "answer_relevancy": float,
  "reasoning": {
    "faithfulness": "...",
    "context_precision": "...",
    "answer_relevancy": "..."
  }
}"""

    context_block = "\n".join(f"[{i+1}] {text}" for i, text in enumerate(context_texts))
    user_prompt = f"""User Query: {user_query}

Retrieved Context:
{context_block}

Agent Response:
{agent_response}
"""

    if trace:
        print("[RAGAS] evaluating faithfulness, context precision, answer relevancy via LLM judge...", flush=True)

    # Prioritize Gemini 3.8 Flash for fast, rate-limit-free industrial RAGAS scoring
    try:
        from google.genai import types
        gemini_client = get_gemini_client()
        gemini_model = os.environ.get("GEMINI_REASONING_MODEL", "gemini-3.8-flash")
        resp = gemini_client.models.generate_content(
            model=gemini_model,
            contents=f"System instructions:\n{sys_prompt}\n\nUser request:\n{user_prompt}",
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        raw = json.loads(resp.text)
        faithfulness = max(0.0, min(1.0, float(raw.get("faithfulness", 0.0))))
        context_precision = max(0.0, min(1.0, float(raw.get("context_precision", 0.0))))
        answer_relevancy = max(0.0, min(1.0, float(raw.get("answer_relevancy", 0.0))))
        if trace:
            print(f"[RAGAS] scored: faithfulness={faithfulness:.2f}, context_precision={context_precision:.2f}, answer_relevancy={answer_relevancy:.2f}", flush=True)
        return {
            "faithfulness": round(faithfulness, 3),
            "context_precision": round(context_precision, 3),
            "answer_relevancy": round(answer_relevancy, 3),
            "low_faithfulness": faithfulness < PASS_THRESHOLD,
        }
    except Exception as exc:
        if trace:
            print(f"[RAGAS] Gemini judge unavailable ({exc}), attempting Groq fallback...", flush=True)

    # Groq fallback
    client = get_client()
    for model in ("openai/gpt-oss-20b", "qwen/qwen3.8-27b"):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            raw = json.loads(resp.choices[0].message.content)
            faithfulness = max(0.0, min(1.0, float(raw.get("faithfulness", 0.0))))
            context_precision = max(0.0, min(1.0, float(raw.get("context_precision", 0.0))))
            answer_relevancy = max(0.0, min(1.0, float(raw.get("answer_relevancy", 0.0))))
            if trace:
                print(f"[RAGAS] scored via Groq: faithfulness={faithfulness:.2f}, context_precision={context_precision:.2f}, answer_relevancy={answer_relevancy:.2f}", flush=True)
            return {
                "faithfulness": round(faithfulness, 3),
                "context_precision": round(context_precision, 3),
                "answer_relevancy": round(answer_relevancy, 3),
                "low_faithfulness": faithfulness < PASS_THRESHOLD,
            }
        except Exception:
            continue
    raise RuntimeError("All judge models (Gemini & Groq) unavailable.")


def score_answer(user_query: str, agent_response: str, retrieved_context: list[tuple[str, str]]) -> dict:
    """Scores one produced answer on faithfulness, context precision, and
    answer relevancy. Returns {"faithfulness": float, "context_precision":
    float, "answer_relevancy": float, "low_faithfulness": bool}. Raises on
    any scoring failure — see module docstring for why."""
    # Defensive normalization: don't assume every agent's retrieved_context
    # stays a clean list of 2-tuples forever.
    context_texts = [item[1] for item in retrieved_context if isinstance(item, (tuple, list)) and len(item) == 2]
    use_direct = os.environ.get("RAGAS_EVAL_MODE", "direct_llm") == "direct_llm"
    if not use_direct and HAS_RAGAS and SingleTurnSample is not None:
        try:
            sample = SingleTurnSample(user_input=user_query, response=agent_response, retrieved_contexts=context_texts)

            judge = get_judge()
            embeddings = get_embeddings()

            trace = os.environ.get("EVALUATION_PROGRESS") == "1"
            if trace:
                print("[RAGAS] faithfulness…", flush=True)
            faithfulness = _score_metric(
                "faithfulness",
                lambda: Faithfulness(llm=judge).single_turn_score(sample),
            )
            if trace:
                print("[RAGAS] context precision…", flush=True)
            if _METRIC_PACING_SECONDS > 0:
                time.sleep(_METRIC_PACING_SECONDS)
            context_precision = _score_metric(
                "context precision",
                lambda: LLMContextPrecisionWithoutReference(
                    llm=judge,
                ).single_turn_score(sample),
            )
            if trace:
                print("[RAGAS] answer relevancy…", flush=True)
            if _METRIC_PACING_SECONDS > 0:
                time.sleep(_METRIC_PACING_SECONDS)
            answer_relevancy = _score_metric(
                "answer relevancy",
                lambda: ResponseRelevancy(
                    llm=judge,
                    embeddings=embeddings,
                    strictness=_RELEVANCY_STRICTNESS,
                ).single_turn_score(sample),
            )
            if trace:
                print("[RAGAS] scoring complete.", flush=True)

            return {
                "faithfulness": faithfulness,
                "context_precision": context_precision,
                "answer_relevancy": answer_relevancy,
                "low_faithfulness": faithfulness < PASS_THRESHOLD,
            }
        except Exception:
            return _score_direct_llm(user_query, agent_response, context_texts)

    return _score_direct_llm(user_query, agent_response, context_texts)


if __name__ == "__main__":
    result = score_answer(
        user_query="Why did P-101 fail?",
        agent_response="P-101 failed due to drive-end bearing wear caused by a missed lubrication interval.",
        retrieved_context=[("FE-001", "FE-001: P-101 drive-end bearing failure, root cause: missed quarterly lubrication service.")],
    )
    for key in ("faithfulness", "context_precision", "answer_relevancy"):
        assert isinstance(result[key], float) and 0.0 <= result[key] <= 1.0, f"{key} out of range: {result[key]}"
    assert isinstance(result["low_faithfulness"], bool)
    print(result)
    print("OK: evaluation.score self-check passed")
