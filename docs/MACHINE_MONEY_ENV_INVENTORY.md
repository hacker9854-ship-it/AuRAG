# AuRAG × Machine Money: Environment, Credentials & Database Inventory

**Document ID:** `DOC-ENV-INVENTORY-2026-09`  
**Purpose:** Comprehensive audit and resetup specification for external APIs, databases, model providers, and Lightning settlement rails.

---

## 1. Credentials & External Services Matrix

| Category | Environment Variable | Required For | Default / Fallback Mode | Where to Obtain / Reset |
|---|---|---|---|---|
| **AI LLM** | `GEMINI_API_KEY` | Structured entity extraction, P&ID vision analysis, OCR fallback | None (Required for live doc ingestion) | [Google AI Studio](https://aistudio.google.com/) |
| **AI LLM** | `GEMINI_REASONING_MODEL` | Deep reasoning engine | `gemini-3.1-flash-lite` | Google AI Studio |
| **AI LLM** | `GEMINI_INGESTION_MODEL` | Fast doc extraction | `gemini-3.1-flash-lite` | Google AI Studio |
| **AI LLM** | `GROQ_API_KEY` | Fast Llama-3 agent reasoning & routing | Required for live Copilot reasoning | [Groq Cloud Console](https://console.groq.com/) |
| **AI LLM** | `GROQ_REASONING_MODEL` | Supervisor agent decisioning | `llama-3.3-70b-versatile` | Groq Console |
| **AI LLM** | `GROQ_ROUTING_MODEL` | Intent classifier | `llama-3.1-8b-instant` | Groq Console |
| **Graph DB** | `NEO4J_URI` | Industrial Knowledge Graph storage | Fallback in-memory mock session active | [Neo4j AuraDB](https://neo4j.com/cloud/aura/) or Local Docker `bolt://localhost:7687` |
| **Graph DB** | `NEO4J_USERNAME` | Neo4j Auth User | `neo4j` | Neo4j Console |
| **Graph DB** | `NEO4J_PASSWORD` | Neo4j Auth Password | `aurag-local-password` | Neo4j Console |
| **Graph DB** | `NEO4J_DATABASE` | Target Database name | `neo4j` | Neo4j Console |
| **Relational DB**| `DATABASE_URL` | Application relational store (Work Orders, Audits, Payments) | Auto-falls back to `sqlite:///.runtime/aurag_enterprise.db` | [Supabase](https://supabase.com/) PostgreSQL or AWS RDS |
| **Vector DB** | `QDRANT_URL` | Hybrid dense semantic chunk index | `http://localhost:6333` | [Qdrant Cloud](https://cloud.qdrant.io/) or Docker |
| **Vector DB** | `QDRANT_API_KEY` | Qdrant Cloud auth token | None (Empty for local) | Qdrant Cloud Console |
| **Reranker** | `COHERE_API_KEY` | Cross-encoder contextual reranking | Optional (`RERANK_PROVIDER=local` uses cross-encoder) | [Cohere Dashboard](https://dashboard.cohere.com/) |
| **Reranker** | `RERANK_PROVIDER` | Search rerank provider | `local` | Set `cohere` or `local` |
| **Cache/Queue** | `REDIS_URL` | Async ingestion pipeline & telemetry message queue | `redis://localhost:6379` | [Upstash Redis](https://upstash.com/) or Docker |
| **Memory** | `MEM0_API_KEY` | User/Operator long-term episodic memory | Falls back to local directory `.runtime/mem0` | [Mem0 Platform](https://mem0.ai/) |
| **Machine Money**| `MACHINE_MONEY_ENABLED` | Master switch for Lightning payment engine | `true` | System Config |
| **Machine Money**| `MACHINE_MONEY_PROVIDER` | Payment backend adapter (`mock`, `lnbits`, `cln`) | `mock` (Zero risk, instant offline testing) | Internal / LNbits Server |
| **Machine Money**| `MACHINE_MONEY_NETWORK` | Bitcoin network identifier (`regtest`, `signet`, `mainnet`) | `regtest` | Bitcoin Node / Wallet |
| **Machine Money**| `MACHINE_MONEY_AUTO_PAY_ENABLED` | Autonomous settlement authorization switch | `false` (Requires operator confirmation by default) | Plant Governance Policy |
| **Machine Money**| `MACHINE_MONEY_MAX_AUTOPAY_SATS`| Maximum satoshis permitted per autonomous transaction | `500` sats | Plant Spending Policy |
| **Machine Money**| `LNBITS_BASE_URL` | Remote LNbits instance URL | `https://legend.lnbits.com` (or local instance) | [LNbits](https://lnbits.com/) |
| **Machine Money**| `LNBITS_ADMIN_KEY` | Server-side wallet payment key (Never exposed to client) | Required only when `MACHINE_MONEY_PROVIDER=lnbits` | LNbits Wallet Details |
| **Machine Money**| `LNBITS_INVOICE_KEY`| Read-only invoice generation key | Optional | LNbits Wallet Details |

---

## 2. Immediate Zero-Dependency Local Setup (Ready to Run)

To allow development, testing, and judge demonstrations without external vendor blocking:
1. **Database:** SQLite is automatically activated in `.runtime/aurag_enterprise.db`.
2. **Knowledge Graph:** `backend/app/core/neo4j.py` automatically uses `FallbackNeo4jSession` with pre-seeded P-101 industrial topology if remote Neo4j is offline.
3. **Machine Money:** `MACHINE_MONEY_PROVIDER=mock` provides deterministic BOLT11 invoice generation, instant verification, and zero satoshi expenditure.
4. **Switching to Live:** When live keys (`GEMINI_API_KEY`, `GROQ_API_KEY`, `LNBITS_ADMIN_KEY`) are pasted into `.env`, the system automatically activates live LLM reasoning and real Lightning settlement.
