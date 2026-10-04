# Devfolio Portal Submission Text: Bitshala BOSS Battle 2026

**Track:** Machine Money Track ($1,000 Prize)  
**Project Name:** AuRAG — Autonomous Industrial Intelligence with Machine Money  
**Repository:** [https://github.com/hacker9854-ship-it/AuRAG](https://github.com/hacker9854-ship-it/AuRAG)  
**Author / Team:** Niss (@hacker9854-ship-it) <mr.hacker9854@gmail.com>

---

## 1. Tagline / One-Liner (Max 140 chars)

> **AuRAG is an industrial GraphRAG agent that detects operational risk, reasons over plant evidence, and settles maintenance over Lightning.**

---

## 2. Project Description (The Elevator Pitch)

In modern industrial facilities (chemical plants, oil refineries, manufacturing lines), predictive AI systems can detect bearing degradation or pump cavitation hours before catastrophic failure occurs. However, **acting** on that predictive insight still takes 24 to 72 hours because procurement and payment rails require manual human intervention: credit cards, purchase orders, vendor invoices, and banking wire approvals. By the time procurement approves a $50 inspection invoice, the pump has seized, causing $250,000 in unbudgeted plant downtime.

**AuRAG solves this by introducing an autonomous Machine Money micro-settlement layer powered by the Bitcoin Lightning Network.**

When industrial sensors detect an anomalous vibration excursion, AuRAG does not simply alert an operator or blindly drain a wallet. It:
1. **Detects** the sensor excursion (`P-101A` vibration spike to $5.8\text{ mm/s}$).
2. **Reasons** over an industrial Neo4j GraphRAG ontology, matching the anomaly to historical failure signature `FE-001`, past work order `WO-1002`, and engineering standard `PROC-001`.
3. **Discovers** pre-approved service providers in its M2M catalog (`maintenance-node-a`) and requests a verifiable quote (250 satoshis for an ultrasonic bearing inspection).
4. **Enforces** zero-trust spending policies (`POL-LIGHTNING-MACHINE-MONEY` with a 500 sat autonomous cap; larger expenses escalate to human digital sign-off).
5. **Settles** the micro-payment in milliseconds over the Bitcoin Lightning Network (BOLT11 invoice), receiving a cryptographic SHA-256 preimage proof.
6. **Records** the complete causal reasoning-to-payment trail in the plant knowledge graph:  
   $$\text{Equipment} \rightarrow \text{PredictiveEvent} \rightarrow \text{WorkOrder} \leftarrow \text{Payment} \rightarrow \text{ServiceProvider}$$

When a plant superintendent asks: *"Why did the machine spend money?"*, AuRAG traverses the graph and provides a verifiable, mathematically grounded explanation backed by a cryptographic audit trail.

---

## 3. How It Was Built (Tech Stack & Architecture)

- **AI & Multi-Agent Orchestration:** LangGraph supervisor coordinating specialist Copilot, RCA, Compliance, and Lessons Learned agents with Groq (`llama-3.3-70b-versatile`) and Gemini 3.1.
- **Knowledge Graph & Ontologies:** Neo4j 5.x property graph linking physical assets, predictive events, work orders, payment transactions, and service providers.
- **Hybrid Retrieval:** Neo4j graph traversal + Qdrant semantic dense embeddings + BM25 keyword search + cross-encoder reranking.
- **Bitcoin Lightning Micro-Settlement Engine:**
  - Pluggable provider abstraction (`LightningProviderInterface`).
  - `MockLightningProvider`: Zero-cost offline deterministic simulation returning valid BOLT11 strings and preimages for judge evaluation.
  - `LNbitsProvider` / `CLN`: Server-side remote wallet adapters moving real satoshis across Lightning channels on `regtest`, `signet`, or `mainnet`.
  - Deterministic idempotency key hashing (`sha256(site:equipment:service:event)`) guaranteeing zero double-spends.
- **Operator Console:** Next.js 16 (App Router), React 19, Tailwind CSS v4, Lucide icons, and dedicated `/machine-money` workspace with interactive SVG BOLT11 QR matrix.
- **Nostr Stretch Readiness (Experimental):** NIP-47-inspired Nostr Wallet Connect simulation (local loopback, HMAC-SHA256 signatures) and NIP-90 (Data Vending Machine `kind: 5100`) telemetry job broadcasting concept.

---

## 4. Challenges & Engineering Highlights

1. **Safety & Zero-Trust Governance:** Giving an autonomous AI an unrestricted wallet is dangerous. We integrated the Machine Money layer directly into AuRAG's automation policy engine. Every transaction is hard-gated by spending caps (500 sats), provider allowlists, and deterministic SHA-256 idempotency. Quotes exceeding 500 sats automatically pause in a `PENDING_APPROVAL` state requiring human sign-off.
2. **Explainability Over Black-Box Spending:** Every payment node in Neo4j carries a `[:FUNDS]` relationship to a work order and `[:PAID_TO]` to a service provider. Causal Cypher queries allow auditing every satoshi back to the exact vibration frequency that triggered it.
3. **Resilient Offline Development & Evaluation:** Judges can evaluate the entire system locally without needing funded mainnet nodes or paid API keys. The system auto-activates SQLite, in-memory Neo4j graph fallbacks, and deterministic mock Lightning providers if live credentials are not present.

---

## 5. Verification & Testing Proof

- **384 Automated Checks Total (100% Passing):**
  - **378 unit/integration tests passing** (317 Backend Pytest + 61 Frontend Vitest).
  - **6 browser E2E checks passing** (Playwright Desktop & Pixel 7 Mobile responsive flows).
  - **384 automated checks total** covering end-to-end integration, failure recovery, and zero regressions.
- **Zero Secrets Committed:** Tested against `.gitignore` with `*.key`, `*.pem`, `*.macaroon` protection.

---

## 6. Project Links & Documentation

- **GitHub Repository:** [https://github.com/hacker9854-ship-it/AuRAG](https://github.com/hacker9854-ship-it/AuRAG)
- **Authoritative Test Snapshot:** [`docs/CURRENT_TEST_SNAPSHOT.md`](./CURRENT_TEST_SNAPSHOT.md)
- **RAGAS Final Verification:** [`docs/RAGAS_FINAL_VERIFICATION.md`](./RAGAS_FINAL_VERIFICATION.md)
- **Claim-to-Evidence Matrix:** [`docs/CLAIM_EVIDENCE_MATRIX.md`](./CLAIM_EVIDENCE_MATRIX.md)
- **Machine Money Verification:** [`docs/MACHINE_MONEY_VERIFICATION.md`](./MACHINE_MONEY_VERIFICATION.md)
- **Judge Demo Script (0:00–5:00):** [`docs/JUDGE_DEMO_SCRIPT.md`](./JUDGE_DEMO_SCRIPT.md)
- **3-Minute Video Demo Script & Storyboard:** [`docs/BOSS_MACHINE_MONEY_DEMO.md`](./BOSS_MACHINE_MONEY_DEMO.md)
- **System Architecture Specification:** [`docs/ARCHITECTURE_MACHINE_MONEY.md`](./ARCHITECTURE_MACHINE_MONEY.md)
- **Historical PRD & Test Archive:** [`docs/archive/`](./archive/)
