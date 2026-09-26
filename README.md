# AuRAG — Industrial Knowledge Intelligence

AuRAG connects plant equipment, failures, work orders, procedures, people,
documents, and regulatory clauses in a Neo4j knowledge graph. A LangGraph
supervisor routes operator questions to Copilot, RCA, Compliance, or Lessons
Learned agents, returning cited answers and an inspectable graph trail.

The current product also includes continuous ingestion, proactive telemetry,
persistent work-order decisions, cross-session mem0 memory, GraphRAG versus
dense-only comparison, knowledge-retirement risk, and a durable RAGAS
evaluation dashboard.

See [PRD.md](./PRD.md), [PRD_CLOSURE.md](./PRD_CLOSURE.md), and
[docs/ACCEPTANCE_REPORT.md](./docs/ACCEPTANCE_REPORT.md).

## Runtime architecture

- `frontend/`: Next.js 16 operator console with separate workspaces.
- `backend/`: FastAPI routes for chat, graph, telemetry, evaluations,
  comparison, ingestion, knowledge risk, notifications, and work orders.
- `agents/`: LangGraph supervisor and four specialist agents.
- `retrieval/`: Neo4j vector, Qdrant dense, BM25, graph traversal, and
  configurable local/Cohere reranking.
- `ingestion/`: clean text, Tesseract plus cloud OCR, Gemini P&ID extraction,
  object storage, Watchdog, Redis, and RQ.
- `telemetry/`: synthetic signal generation, failure-pattern matching, and
  autonomous predictive-event creation.
- `evaluation/`: hard-gated RAGAS scoring and GraphRAG comparison validation.
- `infra/`: Neo4j schema/seed and persistent local Compose services.

## Configuration

Copy `.env.example` to `.env`. Required for the complete local product:

```text
NEO4J_URI
NEO4J_USERNAME
NEO4J_PASSWORD
REDIS_URL
QDRANT_URL
GROQ_API_KEY
GEMINI_API_KEY
MEM0_API_KEY
```

Provider-specific options:

```text
RERANK_PROVIDER=local
COHERE_API_KEY=
CLOUD_OCR_PROVIDER=google_vision
GOOGLE_VISION_API_KEY=
```

The local reranker is the default and requires no Cohere key. Google Cloud
Vision is implemented as the PRD-named low-confidence OCR fallback; `auto`
mode uses it when `GOOGLE_VISION_API_KEY` is present and otherwise retains
the Gemini compatibility fallback.

RAGAS uses `llama-3.3-70b-versatile` by default and fails the acceptance gate
on provider errors, missing scores, or any metric below `0.70`.
`GROQ_REASONING_MODEL` and `GROQ_ROUTING_MODEL` can override the agent models
when a provider model is temporarily quota-limited.

## Bootstrap and run

From the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1 -SkipInstall -SkipInfra -InitializeData
```

Start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend:

```powershell
npm.cmd --prefix frontend run dev
```

Optional workers:

```powershell
.\.venv\Scripts\python.exe -m telemetry.worker
.\.venv\Scripts\python.exe -m ingestion.workers.watcher
.\.venv\Scripts\rq.exe worker aurag-ingest
```

For managed deployments, documents should be uploaded through
`POST /api/ingestion/documents`; the API writes an immutable object to shared
S3-compatible storage and enqueues the same RQ ingestion pipeline.

## Verification

Backend and domain tests:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider
```

Frontend:

```powershell
npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend run test:e2e
npm.cmd --prefix frontend run test:e2e:live
npm.cmd --prefix frontend audit --omit=dev
```

The normal Playwright suite uses deterministic API fixtures for UI behavior.
`test:e2e:live` is a separate non-mocked gate that submits a real question to
FastAPI, renders graph evidence, and loads real mobile knowledge-risk data.

Provider-backed acceptance:

```powershell
docker build -t aurag:acceptance .

docker run --rm --env-file .env `
  -e NEO4J_URI=bolt://host.docker.internal:7687 `
  -e NEO4J_USERNAME=neo4j `
  -e NEO4J_PASSWORD=aurag-local-password `
  -e QDRANT_URL=http://host.docker.internal:6333 `
  -e REDIS_URL=redis://host.docker.internal:6379/0 `
  -v aurag_acceptance_hf_cache:/home/aurag/.cache/huggingface `
  aurag:acceptance python -m evaluation.validate_ragas
```

Live mem0 proof:

```powershell
$proofId = [guid]::NewGuid().ToString('N')
docker run --rm --env-file .env `
  -e PROOF_ID=$proofId `
  -e PYTHONPATH=/app `
  -v "${PWD}/scripts/validate_mem0.py:/tmp/validate_mem0.py:ro" `
  aurag:acceptance python /tmp/validate_mem0.py
```

Backend smoke:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke.ps1
```

## Deployment

- `render.yaml` defines the API, telemetry worker, and RQ ingestion worker.
- `frontend/vercel.json` defines the frontend build.
- `BACKEND_CORS_ORIGINS` must contain the exact deployed frontend origin.
- Render/Vercel URLs and cloud smoke evidence require access to those
  accounts; configuration files alone are not deployment proof.

See [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md).

## Current external evidence gaps

As of July 25, 2026:

- No Render or Vercel account access is available, so hosted URLs, deployed
  browser acceptance, deck upload, and demo video are not proven.
- Cohere reranking is live-validated.
- Google Vision OCR reaches the provider, but its configured Google Cloud
  project has billing disabled and returns HTTP 403.
- The public 42-page P&ID course document uses tags unrelated to the
  synthetic plant. Two manually reviewed diagram pages are provider-validated;
  it is not valid evidence for plant-specific `CONNECTED_TO` relationships.
