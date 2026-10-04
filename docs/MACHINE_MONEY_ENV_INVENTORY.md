# AuRAG × Machine Money: Complete API, Secrets & Environment Inventory

**Document Reference:** `DOC-ENV-INVENTORY-2026-TASK8`  
**Applicability:** Bitshala BOSS Battle 2026 — Machine Money Track  
**Classification:** Confidential Developer Guide (DO NOT COMMIT REAL SECRETS)

> [!IMPORTANT]
> **Zero-Knowledge Security Directive:**  
> Never paste secret keys, wallet admin seeds, or tokens into shared chat interfaces.  
> Enter secret values **locally** in your untracked `.env` or `.env.local` file.  
> This document details every environment variable, its purpose, scope, acquisition source, and automated connectivity check.

---

## 1. System-Wide Environment Variable Matrix

| Category | Variable Name | Purpose | Where to Obtain | Scope | Offline Default / Mock |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AI LLM** | `GEMINI_API_KEY` | Structured entity extraction & vision analysis | [Google AI Studio](https://aistudio.google.com/) | Server-Only | Mock extractor fallback |
| **AI LLM** | `GEMINI_REASONING_MODEL` | Gemini model name for reasoning | Google AI Studio | Server-Only | `gemini-3.1-flash-lite` |
| **AI LLM** | `GEMINI_INGESTION_MODEL` | Gemini model name for ingestion | Google AI Studio | Server-Only | `gemini-3.1-flash-lite` |
| **AI LLM** | `GROQ_API_KEY` | Fast agent routing & supervisor copilot | [Groq Cloud Console](https://console.groq.com/) | Server-Only | Mock reasoning fallback |
| **AI LLM** | `GROQ_REASONING_MODEL` | Groq Llama-3 model ID | Groq Cloud Console | Server-Only | `llama-3.3-70b-versatile` |
| **AI LLM** | `GROQ_ROUTING_MODEL` | Fast intent classification model | Groq Cloud Console | Server-Only | `llama-3.1-8b-instant` |
| **AI LLM** | `GROQ_JUDGE_MODEL` | Ragas LLM judge evaluation | Groq Cloud Console | Server-Only | `llama-3.3-70b-versatile` |
| **Graph DB** | `NEO4J_URI` | Industrial Knowledge Graph Bolt endpoint | [Neo4j AuraDB](https://neo4j.com/cloud/aura/) / Docker | Server-Only | `FallbackNeo4jSession` (in-memory) |
| **Graph DB** | `NEO4J_USERNAME` | Neo4j database username | Neo4j Console | Server-Only | `neo4j` |
| **Graph DB** | `NEO4J_PASSWORD` | Neo4j database password | Neo4j Console | Server-Only | `aurag-local-password` |
| **Graph DB** | `NEO4J_DATABASE` | Target database catalog | Neo4j Console | Server-Only | `neo4j` |
| **Vector DB** | `QDRANT_URL` | Semantic vector chunk search endpoint | [Qdrant Cloud](https://cloud.qdrant.io/) / Docker | Server-Only | `http://localhost:6333` |
| **Vector DB** | `QDRANT_API_KEY` | Qdrant Cloud API token | Qdrant Cloud Console | Server-Only | None (local mode) |
| **Retrieval** | `COHERE_API_KEY` | Cross-encoder reranking | [Cohere Dashboard](https://dashboard.cohere.com/) | Server-Only | Optional (`RERANK_PROVIDER=local`) |
| **Retrieval** | `COHERE_RERANK_MODEL` | Cohere rerank model identifier | Cohere Dashboard | Server-Only | `rerank-v4.0-pro` |
| **Retrieval** | `RERANK_PROVIDER` | Active reranking engine | System Config | Server-Only | `local` |
| **Memory** | `MEM0_API_KEY` | Episodic operator memory | [Mem0 Platform](https://mem0.ai/) | Server-Only | Local directory `.runtime/mem0` |
| **Memory** | `MEM0_DIR` | Local state directory for episodic memory | Local filesystem | Server-Only | `.runtime/mem0` |
| **Infra** | `REDIS_URL` | Telemetry & ingestion task queue | [Upstash Redis](https://upstash.com/) / Docker | Server-Only | `redis://localhost:6379` |
| **Infra** | `DATABASE_URL` | SQL store for payments & work orders | PostgreSQL / SQLite | Server-Only | `sqlite:///.runtime/aurag_enterprise.db` |
| **Infra** | `AWS_ACCESS_KEY_ID` | Optional S3 object storage | AWS IAM Console | Server-Only | Local file storage (`INGEST_STORAGE_BACKEND=local`) |
| **Infra** | `AWS_DEFAULT_REGION` | AWS Region | AWS Console | Server-Only | `us-east-1` |
| **Infra** | `AWS_REGION` | AWS Region alias | AWS Console | Server-Only | `us-east-1` |
| **OCR / Cloud**| `GOOGLE_VISION_API_KEY` | P&ID engineering diagram OCR | [Google Cloud Console](https://console.cloud.google.com/) | Server-Only | Tesseract / Gemini fallback |
| **Frontend** | `NEXT_PUBLIC_API_URL` | Next.js API client endpoint | Deployment URL | Public | `http://localhost:8000` |
| **Frontend** | `BACKEND_URL` | Server-side backend proxy target | Deployment URL | Server-Only | `http://localhost:8000` |
| **Frontend** | `API_URL` | Internal API route alias | Deployment URL | Server-Only | `http://localhost:8000` |
| **Frontend** | `NEXT_PUBLIC_SITE_ID` | Plant site identifier for frontend | Plant Config | Public | `plant-mumbai-01` |
| **Frontend** | `SITE_ID` | Plant site identifier for backend | Plant Config | Server-Only | `plant-mumbai-01` |
| **Frontend** | `BACKEND_CORS_ORIGINS`| Permitted CORS origin list | System Config | Server-Only | `http://localhost:3000,http://localhost:3001` |
| **Enterprise** | `ENTRA_CLIENT_ID` | Azure AD / Entra ID client ID | Azure Portal | Server-Only | None (Optional RBAC) |
| **Enterprise** | `ENTRA_TENANT_ID` | Azure AD Tenant ID | Azure Portal | Server-Only | None (Optional RBAC) |
| **Enterprise** | `ENTRA_JWKS_URI` | OpenID JWKS verification URL | Azure Portal | Server-Only | None (Optional RBAC) |
| **Enterprise** | `BEDROCK_REASONING_MODEL`| AWS Bedrock model identifier | AWS Bedrock | Server-Only | None (Optional fallback) |
| **Enterprise** | `BEDROCK_ROUTING_MODEL` | AWS Bedrock router model | AWS Bedrock | Server-Only | None (Optional fallback) |
| **Enterprise** | `LLM_PROVIDER` | Primary LLM provider selection | System Config | Server-Only | `groq` |
| **Enterprise** | `LOCAL_MODEL_NAME` | Local HuggingFace embedding/LLM | HuggingFace | Server-Only | `BAAI/bge-small-en-v1.5` |
| **Machine Money** | `MACHINE_MONEY_ENABLED` | Master switch for Lightning subsystem | System Config | Server-Only | `true` |
| **Machine Money** | `MACHINE_MONEY_PROVIDER` | Adapter (`mock`, `lnbits`, `cln`) | System Config | Server-Only | `mock` (Zero cost simulation) |
| **Machine Money** | `MACHINE_MONEY_NETWORK` | Network (`regtest`, `signet`, `mainnet`)| Bitcoin Node / Wallet | Server-Only | `regtest` |
| **Machine Money** | `MACHINE_MONEY_AUTO_PAY_ENABLED` | Autonomous settlement authorization switch | Plant Policy | Server-Only | `true` |
| **Machine Money** | `MACHINE_MONEY_MAX_AUTOPAY_SATS` | Max sats allowed per autonomous payment | Plant Policy | Server-Only | `500` sats |
| **Machine Money** | `MACHINE_MONEY_AUTO_PAY_THRESHOLD_SATS` | Human-in-the-loop escalation limit | Plant Policy | Server-Only | `500` sats |
| **Machine Money** | `MACHINE_MONEY_PROVIDER_ALLOWLIST` | Permitted service provider node IDs | Vendor Registry | Server-Only | Pre-registered catalog |
| **Machine Money** | `LNBITS_BASE_URL` | LNbits API instance URL | [LNbits.com](https://lnbits.com/) / Self-hosted | Server-Only | `https://legend.lnbits.com` |
| **Machine Money** | `LNBITS_ADMIN_KEY` | Wallet payment admin key (Secret!) | LNbits Wallet Details | Server-Only | Required for live LNbits |
| **Machine Money** | `LNBITS_INVOICE_KEY` | Read-only invoice generation key | LNbits Wallet Details | Server-Only | Optional |
| **Machine Money** | `CLN_RPC_URL` | Core Lightning RPC endpoint | CLN node | Server-Only | `https://127.0.0.1:9735` |
| **Machine Money** | `CLN_RPC_USER` | CLN RPC username | CLN node | Server-Only | `cln_rpc_user` |
| **Machine Money** | `CLN_RPC_PASSWORD` | CLN RPC password | CLN node | Server-Only | `cln_password` |
| **Machine Money** | `CLN_MACAROON_PATH` | Path to CLN access macaroon | CLN node | Server-Only | `~/.lightning/access.macaroon` |
| **Machine Money** | `NWC_CONNECTION_STRING` | NIP-47 Nostr Wallet Connect URI | Alby / Mutiny / Nostr Wallet | Server-Only | Optional stretch |

---

## 2. Live Connectivity Check Recipes

To verify that credentials are functioning properly without running the entire application:

### A. Groq API Check
```bash
curl -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "ping"}]}'
```

### B. Gemini API Check
```bash
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents": [{"parts":[{"text": "ping"}]}]}'
```

### C. Neo4j Graph Database Check
```python
from neo4j import GraphDatabase
import os

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "aurag-local-password")

driver = GraphDatabase.driver(uri, auth=(user, password))
driver.verify_connectivity()
print("Neo4j Connected Successfully!")
```

### D. LNbits Lightning Wallet Check
```bash
curl -X GET "$LNBITS_BASE_URL/api/v1/wallet" \
  -H "X-Api-Key: $LNBITS_ADMIN_KEY"
```
*Expected Response:* `{"id": "...", "name": "...", "balance": 1000000}`

### E. Machine Money Subsystem Health Check
Once the AuRAG backend is running:
```bash
curl -X GET http://localhost:8000/api/machine-money/health
```
*Expected Response:*
```json
{
  "provider_name": "MockLightningProvider",
  "is_connected": true,
  "network": "regtest",
  "balance_sats": 1000000,
  "node_pubkey": "02mockpubkey0000000000000000000000000000000000000000000000000000000001",
  "details": {
    "settlement_latency_ms": 15,
    "demo_mode": true
  }
}
```

---

## 3. Zero-Dependency Offline Execution Mode

AuRAG is engineered with zero-vendor fallback redundancy:
1. **Mock Lightning Provider:** When `MACHINE_MONEY_PROVIDER=mock`, the system generates verifiable BOLT11 invoices, computes sha256 preimages, validates spending limits, and tracks balances with zero Bitcoin spend and zero network dependency.
2. **In-Memory Graph Fallback:** When Neo4j Aura is unavailable, `backend/app/core/neo4j.py` automatically initializes an in-memory graph containing equipment nodes (`P-101A`, `C-201`), failure signatures (`FE-001`), work orders (`WO-1002`), and payment relationships.
3. **Local SQLite DB:** Automatically initialized at `.runtime/aurag_enterprise.db` when PostgreSQL is not configured.
4. **Deterministic Idempotency:** Guard hashes prevent duplicate invoice settlement under simulated or live rails.
