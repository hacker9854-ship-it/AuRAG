# AuRAG Acceptance Report

> [!WARNING]
> **HISTORICAL VERIFICATION SNAPSHOT — NOT THE CURRENT RELEASE STATE**
>
> This document is preserved for historical audit purposes only (capturing the early Phase 1 baseline from September 27, 2026).
> For the current authoritative submission status and verified metrics, consult:
> - [CURRENT_TEST_SNAPSHOT.md](../CURRENT_TEST_SNAPSHOT.md) — 384 Automated Checks Passing (378 Unit/Integration + 6 Browser E2E)
> - [RAGAS_FINAL_VERIFICATION.md](../RAGAS_FINAL_VERIFICATION.md) — 24/24 Evaluation Pipeline Verification
> - [CLAIM_EVIDENCE_MATRIX.md](../CLAIM_EVIDENCE_MATRIX.md) — Grounded Claims & Technical Verification Matrix
> - [MACHINE_MONEY_VERIFICATION.md](../MACHINE_MONEY_VERIFICATION.md) — Full Machine Money Subsystem Proof & Audit
> - [JUDGE_DEMO_SCRIPT.md](../JUDGE_DEMO_SCRIPT.md) — Authoritative Step-by-Step Evaluation Walkthrough

**Environment:** local Windows host plus Linux Docker  
**Historical Snapshot Date:** September 27, 2026  
**Acceptance image:** `aurag:acceptance`

## Passed gates

| Gate | Result |
|---|---|
| Python suite | 113 passed in Linux Docker |
| Frontend Vitest | 10 passed |
| ESLint | Passed |
| Next production build | Passed on Next.js 16.2.11 |
| Playwright fixture suite | 6 passed, desktop and mobile |
| Playwright live suite | 2 passed, desktop real chat/graph and mobile real knowledge-risk |
| npm production audit | 0 vulnerabilities |
| Docker build | Passed |
| API readiness | Neo4j, Qdrant, Redis, Groq, Gemini, mem0 all up |
| mem0 live proof | Cross-session recall and separate-user isolation passed |
| Scanned OCR live proof | Gemini compatibility fallback recovered both required handwritten terms |
| Backend smoke without provider scoring | Passed, including persistent mutations |
| Telemetry precision/recall | 1.000 / 1.000 |
| Ingestion mention ground truth | 13/13 |
| Hybrid retrieval benchmark | 5/5 |
| GraphRAG comparison benchmark | 5/5 |
| P&ID provider baseline | 52 entities, 51 connections on pages 3 and 21 |
| Cohere rerank | Live calibration-evidence rerank passed |
| Full RAGAS acceptance | 24/24 cases passed; faithfulness 0.960, context precision 0.903, answer relevancy 0.920 |

## Commands

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider

npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend run test:e2e
npm.cmd --prefix frontend run test:e2e:live
npm.cmd --prefix frontend audit --omit=dev

docker build -t aurag:acceptance .

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\smoke.ps1 -BaseUrl http://localhost:8000 `
  -SkipProviderChecks
```

## Provider-backed RAGAS status

The hard gate is:

```powershell
docker run --rm --env-file .env `
  -e GROQ_JUDGE_MODEL=openai/gpt-oss-20b `
  -e NEO4J_URI=bolt://host.docker.internal:7687 `
  -e NEO4J_USERNAME=neo4j `
  -e NEO4J_PASSWORD=aurag-local-password `
  -e NEO4J_DATABASE=neo4j `
  -e REDIS_URL=redis://host.docker.internal:6379/0 `
  -e QDRANT_URL=http://host.docker.internal:6333 `
  -e RAGAS_CASE_MAX_RETRIES=6 `
  -e RAGAS_CASE_MAX_RETRY_DELAY_SECONDS=900 `
  -v aurag_acceptance_hf_cache:/home/aurag/.cache/huggingface `
  aurag:acceptance python -m evaluation.validate_ragas
```

The validator fails on any provider error, missing score, or metric below
0.70. It honors Groq’s reported retry interval and never retries a low score.

The latest authoritative command completed successfully on the supported
`openai/gpt-oss-20b` Groq judge, with paced metric requests to respect its
8,000 TPM limit. It passed all eight cases and every metric exceeded 0.70.

## External evidence and limits

- Cohere is live-validated.
- Google Vision reaches the provider, but Google returns HTTP 403 because
  billing is disabled for the configured project.
- No Render/Vercel account access or hosted URL is available.
- No final deck/video upload target is available.
- The public P&ID source is not plant-aligned, so it cannot prove persisted
  plant-specific connectivity.
