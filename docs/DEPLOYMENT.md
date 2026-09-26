# AuRAG Deployment

AuRAG deploys as a FastAPI Docker service and background workers on Render,
with the Next.js frontend on Vercel. Neo4j, Qdrant, Redis, Groq, Gemini,
mem0, Cohere, Google Vision, and S3-compatible ingestion storage are managed
dependencies.

## Local bootstrap

Requirements:

- Python 3.12
- Node.js 22+
- Docker Desktop
- PowerShell 5.1 or 7

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\bootstrap.ps1

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\bootstrap.ps1 `
  -SkipInstall -SkipInfra -InitializeData
```

The first command creates missing local configuration/dependencies and starts
Neo4j, Qdrant, and Redis. The second applies the idempotent schema/seed and
rebuilds vector indexes.

## Local runtime

```powershell
.\.venv\Scripts\python.exe -m uvicorn `
  backend.app.main:app --host 127.0.0.1 --port 8000

npm.cmd --prefix frontend run dev
```

Optional workers:

```powershell
.\.venv\Scripts\python.exe -m telemetry.worker
.\.venv\Scripts\python.exe -m ingestion.workers.watcher
.\.venv\Scripts\rq.exe worker aurag-ingest
```

The Watchdog process is for local/shared-folder operation. In managed cloud
deployment, use `POST /api/ingestion/documents`: the API writes the upload to
shared S3-compatible object storage and enqueues the same RQ worker. Render
service filesystems are not treated as a shared upload directory.

## Container

```powershell
docker build -t aurag:acceptance .

docker run --rm -p 8000:8000 --env-file .env `
  -e NEO4J_URI=bolt://host.docker.internal:7687 `
  -e QDRANT_URL=http://host.docker.internal:6333 `
  -e REDIS_URL=redis://host.docker.internal:6379/0 `
  aurag:acceptance
```

The image uses Python 3.12, runs as an unprivileged user, includes Tesseract,
excludes `.env`, and exposes `/api/health/live` as its process health check.

## Render Blueprint

`render.yaml` defines:

- `aurag-api`: FastAPI web service;
- `aurag-telemetry`: proactive telemetry worker;
- `aurag-ingest-queue`: RQ ingestion worker.

Required `sync: false` values:

```text
NEO4J_URI
NEO4J_USERNAME
NEO4J_PASSWORD
QDRANT_URL
QDRANT_API_KEY
REDIS_URL
GROQ_API_KEY
GEMINI_API_KEY
COHERE_API_KEY
GOOGLE_VISION_API_KEY
MEM0_API_KEY
BACKEND_CORS_ORIGINS
INGEST_S3_BUCKET
INGEST_S3_ENDPOINT
INGEST_S3_REGION
INGEST_S3_ACCESS_KEY_ID
INGEST_S3_SECRET_ACCESS_KEY
```

`QDRANT_API_KEY` and `INGEST_S3_ENDPOINT` are optional when the selected
providers do not require them. `COHERE_API_KEY` is required when
`RERANK_PROVIDER=cohere`. `GOOGLE_VISION_API_KEY` is required when
`CLOUD_OCR_PROVIDER=google_vision`.

Initialize production data from a trusted one-off job using the same
environment:

```text
python -m ingestion.loader.load_seed
python -m retrieval.index_chunks
```

Render health checks use `/api/health/live`. Operational acceptance uses
`/api/health/ready`, which verifies Neo4j, Qdrant, Redis, required model keys,
and the constructed mem0 client. Readiness is not a substitute for the live
provider acceptance commands in `docs/ACCEPTANCE_REPORT.md`.

## Vercel

Create a Vercel project with `frontend` as the project root.
`frontend/vercel.json` runs the existing clean install and production build.

Set:

```text
NEXT_PUBLIC_API_URL=https://<render-api-host>
```

Set the backend’s Render variable to the exact frontend origin:

```text
BACKEND_CORS_ORIGINS=https://<vercel-host>
```

Comma-separated origins are supported for intentional preview hosts. Redeploy
the frontend after changing `NEXT_PUBLIC_API_URL` because Next.js embeds
public environment values at build time.

## Smoke and browser acceptance

Local:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\smoke.ps1 `
  -BaseUrl http://localhost:8000

npm.cmd --prefix frontend run test:e2e:live
```

Hosted:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\smoke.ps1 `
  -BaseUrl https://<render-api-host>
```

Then run the live Playwright spec with `NEXT_PUBLIC_API_URL` set to the
hosted API and the web server pointed at the deployed Vercel URL, or perform
the equivalent recorded browser walkthrough.

The smoke’s final section intentionally creates a predictive event and a work
order that ends in `Rejected`. Use `-SkipMutatingChecks` only when mutation is
not authorized.

## CI

`.github/workflows/ci.yml` has backend, frontend, and delivery jobs. CI covers
unit/integration tests, lint, production build, and static delivery checks.
Live provider and hosted-browser gates remain explicit release steps because
they require secrets, managed services, and mutation authority.

## Release checklist

1. CI and the current local acceptance suites are green.
2. Production Neo4j/Qdrant data and indexes are initialized.
3. Every required provider/storage secret is configured.
4. `/api/health/live` and `/api/health/ready` pass.
5. The all-eight RAGAS hard gate exits zero.
6. The full smoke passes against Render.
7. The real Vercel browser completes investigation, graph, comparison,
   telemetry notification, work-order decision, evaluation, and knowledge
   risk flows.
8. The demo script is rehearsed and the deck/video artifacts are uploaded.
