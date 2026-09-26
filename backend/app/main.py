"""FastAPI app — Phase 8 adapter layer. Every endpoint is a thin wrapper
around already-built, already-tested pure functions from agents/telemetry/
evaluation (Phases 4-7); no business logic lives here. Run from repo root:

    uvicorn backend.app.main:app --reload
"""
import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path regardless of where uvicorn is launched
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse

from backend.app.api import (
    automations,
    chat,
    comparison,
    connectors,
    equipment,
    evaluations,
    events,
    graph,
    health,
    ingestion,
    knowledge_risk,
    telemetry,
    work_orders,
)
from backend.app.db.database import init_db

# Initialize relational tables
init_db()

app = FastAPI(title="AuRAG Operator Console API")


def cors_origins() -> list[str]:
    configured = os.environ.get(
        "BACKEND_CORS_ORIGINS",
        "*",
    )
    if not configured or configured.strip() == "*":
        return ["*"]
    origins = [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]
    if "*" not in origins:
        origins.append("*")
    return origins

# ponytail: wide-open localhost dev origins, no auth — matches the project's
# standing "no auth/permissions" ground rule and this being a local demo app,
# not a deployed multi-tenant service. Both common Next.js dev ports: Next
# falls back to 3001 if 3000 is already taken.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
def root():
    return {"status": "ok", "service": "AuRAG Operator Console API"}


@app.exception_handler(HTTPException)
def flat_http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = {"error": str(exc.detail), "detail": str(exc.detail)}
    # Prevent Render / Cloudflare reverse proxy from converting 5xx into HTML 502 with dropped CORS
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    if exc.status_code >= 500:
        return JSONResponse(status_code=200, content={"error": "service_degraded", **content}, headers=headers)
    return JSONResponse(status_code=exc.status_code, content=content, headers=headers)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    return JSONResponse(
        status_code=200,
        content={"error": "internal_error", "detail": str(exc), "traceback": traceback.format_exc()},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )



app.include_router(chat.router, prefix="/api")
app.include_router(equipment.router, prefix="/api")
app.include_router(telemetry.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(ingestion.router, prefix="/api")
app.include_router(knowledge_risk.router, prefix="/api")
app.include_router(comparison.router, prefix="/api")
app.include_router(evaluations.router, prefix="/api")
app.include_router(work_orders.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(connectors.router, prefix="/api")
app.include_router(automations.router, prefix="/api")


# On Render free tier (512MB RAM), pre-warming torch and sentence_transformers
# causes the kernel OOM killer to immediately terminate the instance.
# Models will only be lazy-loaded on demand if requested.

