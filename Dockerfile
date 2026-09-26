# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm AS builder

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN python -m venv "${VIRTUAL_ENV}"

COPY requirements.lock ./

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip==26.1.1 \
    && python -m pip install -r requirements.lock \
    && python -m pip install "pyjwt>=2.8.0" "cryptography>=42.0.0"

ENV HF_HOME=/root/.cache/huggingface
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"


FROM python:3.12-slim-bookworm AS runtime

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MEM0_DIR=/app/.runtime/mem0 \
    HF_HOME=/app/.cache/huggingface

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        ca-certificates \
        libglib2.0-0 \
        libgomp1 \
        tesseract-ocr \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin aurag

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder --chown=aurag:aurag /root/.cache/huggingface /app/.cache/huggingface

COPY --chown=aurag:aurag agents agents
COPY --chown=aurag:aurag backend backend
COPY --chown=aurag:aurag data data
COPY --chown=aurag:aurag evaluation evaluation
COPY --chown=aurag:aurag infra infra
COPY --chown=aurag:aurag ingestion ingestion
COPY --chown=aurag:aurag retrieval retrieval
COPY --chown=aurag:aurag telemetry telemetry

RUN mkdir -p /app/data/incoming /app/.runtime/mem0 \
    && chown -R aurag:aurag /app

USER aurag

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os, urllib.request; p = os.environ.get('PORT', '10000'); urllib.request.urlopen('http://127.0.0.1:%s/api/health/live' % p, timeout=3)"

CMD ["sh", "-c", "exec uvicorn backend.app.main:app --host 0.0.0.0 --port \"${PORT:-10000}\""]
