# PRD: AuRAG — Autonomous Industrial Intelligence & Machine Money

**Bitshala BOSS Battle 2026 — Machine Money Track**

---

## 1. Problem Statement

Asset-intensive industries lose ~35% of working hours searching for information scattered across 7–12 disconnected document systems (McKinsey 2024 / NASSCOM-EY). This fragmentation contributes to 18–22% of unplanned downtime (BIS Research), and a "knowledge cliff" looms as ~25% of India's experienced industrial engineers retire within a decade, taking undocumented operational knowledge with them.

**Our thesis:** This is not a file-management problem — it's a graph problem. Equipment, failures, procedures, personnel, and regulations are all *connected entities*, and the fragmentation is really a **missing relationship layer**, not a missing search bar.

---

## 2. Goal

Build a **Unified Operations Agent** — a single conversational interface, backed by a Neo4j knowledge graph, that understands user intent and routes to the right underlying capability (visualize, diagnose root cause, check compliance, surface hidden patterns) — rather than five disconnected point solutions.

**North Star Demo Moment:** Ask one natural-language question → watch the system reason over the graph (not just retrieve a paragraph) → get a cited, connected, actionable answer that a plain-RAG/keyword-search system could not have produced.

---

## 3. Non-Goals (Explicitly Out of Scope)

- Production-grade auth/permissions/multi-tenancy
- Native mobile app (responsive web is sufficient to demonstrate the "mobile-first" requirement)

---

## 4. Architecture Overview

```
FRONTEND — Next.js 16 + Tailwind v4 + Neovis.js/NVL
(Chat + Graph Viz + Telemetry Slider + RAGAS Dashboard)
                    |
                    v
SUPERVISOR AGENT (LangGraph) — Intent Router
Decides which specialized agent handles this query
    |         |          |           |
    v         v          v           v
Copilot   RCA Agent  Compliance  Lessons Learned
Agent     (dedicated  Agent      Agent
          reasoning   (dedicated (pattern
          chain)      reasoning  detection)
                       chain)
    |         |          |           |
    +---------+----------+-----------+
                    |
                    v
HYBRID RETRIEVAL LAYER
Neo4j (graph traversal + native vector) + Qdrant (dense) +
BM25 (keyword/exact-match) -> Cohere Rerank -> best context
                    |
                    v
         Neo4j Graph (source of truth)
                    ^
                    |
         Ingestion + mem0 (cross-session memory layer)

[Parallel] Proactive Intelligence Layer:
Synthetic Telemetry Feed -> pattern-match against graph ->
auto-draft work order -> push to UI (before user asks)

[Parallel] Evaluation Layer:
RAGAS scores every Copilot answer (faithfulness, context
precision, answer relevancy) -> live quality dashboard
```

**Key architectural decision:** A **Supervisor + specialized sub-agents** pattern (LangGraph), not one generic prompt handling every intent. Each domain (RCA, Compliance, Lessons Learned) gets its own reasoning chain tuned to that task, which produces more consistent, higher-quality output than a single generalist prompt switching context on the fly. The Supervisor's only job is correct routing — it does not do the domain reasoning itself.

**Why this beats a single-agent router for a "perfection" bar:** A single LLM juggling four very different reasoning styles (visualization formatting vs. root-cause diagnosis vs. regulatory gap analysis vs. cross-incident pattern-mining) tends to produce shallower answers on some intents as prompt complexity grows. Dedicated sub-agents let each reasoning chain be deeply tuned and independently tested — directly serving the "Technical Excellence" and "query answer quality" evaluation criteria in the brief.

**Why hybrid retrieval over Neo4j-vector-only:** Semantic (vector) search alone can retrieve plausible-sounding but wrong context — e.g. conflating two similarly-worded equipment descriptions. BM25 keyword matching guarantees exact-term hits (equipment tags, clause IDs) that vector search can miss, and Cohere reranking combines both signals into a single best-ranked context set before it reaches a sub-agent.

---

## 5. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Graph + Vector DB | Neo4j AuraDB | Source of truth; native vector index + graph together |
| Dense vector store | Qdrant | Dedicated high-recall dense retrieval, complements Neo4j vector index |
| Keyword retrieval | BM25 (`rank_bm25` or Elasticsearch) | Guarantees exact-term hits (equipment tags, clause IDs) that embeddings can miss |
| Reranking | Cohere Rerank | Merges dense + keyword candidates into one best-ranked context set |
| Multi-agent orchestration | LangGraph | Supervisor + specialized sub-agent graphs, explicit state passing between nodes |
| LLMs | **Groq** (Llama 3.3/Mixtral, via Groq's fast inference) for Supervisor/routing; **Gemini** for RCA/Compliance/Lessons-Learned agents and vision tasks | Groq's low latency suits the routing step; Gemini's multimodal + long-context strength suits deep reasoning and P&ID vision parsing; both have usable free tiers |
| Cross-session memory | mem0 | Lets the system recall prior sessions/queries — satisfies the brief's "continuously updated" requirement literally |
| Evaluation | RAGAS | Scores every Copilot answer on faithfulness, context precision, answer relevancy — turns "trust us" into a number |
| Entity extraction | LLM structured JSON output | Reliable, no custom NER training needed |
| Ingestion | Python + `pdfplumber` / `pytesseract` (if scanned) | Standard document parsing |
| Graph visualization | Neovis.js / NVL | Renders live graph state in the browser |
| Frontend | Next.js 16 + Tailwind CSS v4 | Full app router, server components, fast iteration |
| Backend | FastAPI (Python) | Orchestration endpoints, plays well with LangGraph/Neo4j/Qdrant clients |
| Proactive layer | Synthetic telemetry generator (Python) + rule/pattern match against graph | Drives the auto-draft-work-order "wow" feature |
| Continuous ingestion queue | Redis + RQ | Decouples file-detection from heavy OCR/CV/extraction processing — same async/resilience guarantee as a full message broker (Kafka/RabbitMQ), without the disproportionate operational overhead at this scale |
| Hosting (demo) | Vercel (frontend) + Railway/Render (backend) | Live shareable deployment for judges |

---

## 6. Data Model (Neo4j Schema)

**Nodes:**
- `Equipment` (tag_id, type, location, criticality)
- `Document` (id, type, title, date, source_file)
- `Chunk` (text, embedding, page_ref)
- `Person` (name, role, department, years_to_retirement)
- `WorkOrder` (id, date, type, status)
- `FailureEvent` (id, date, symptom, root_cause)
- `RegulatoryClause` (source, clause_id, requirement_text)
- `Procedure` (id, title, version)

**Relationships:**
- `(Document)-[:CONTAINS]->(Chunk)`
- `(Chunk)-[:MENTIONS]->(Equipment | Person)`
- `(Equipment)-[:HAS_PART]->(Equipment)`
- `(WorkOrder)-[:PERFORMED_ON]->(Equipment)`
- `(WorkOrder)-[:PERFORMED_BY]->(Person)`
- `(FailureEvent)-[:OCCURRED_ON]->(Equipment)`
- `(FailureEvent)-[:DOCUMENTED_IN]->(Document)`
- `(Procedure)-[:GOVERNS]->(Equipment)`
- `(RegulatoryClause)-[:APPLIES_TO]->(Equipment | Procedure)`

---

## 7. Data Sourcing Strategy

| Data type | Source | Real or Synthetic |
|---|---|---|
| Regulatory clauses | OISD.gov.in, Factory Act 1948 (public PDFs) | **Real** — boosts compliance-feature credibility |
| Sample P&IDs / equipment manuals | Public manufacturer PDFs (search "sample P&ID PDF") | Real (public samples) |
| Equipment list, failure history, work orders | Self-authored fictional plant (10–15 equipment tags) | Synthetic — necessary, no privacy concern |

**Principle:** Reference/context data = real where possible (credibility). Operational/transactional data = synthetic (necessary and expected by judges).

---

## 8. Full Feature Scope

All of the following ship — no cutting for time, since the goal is the most complete, rigorous system rather than a minimal MVP.

1. **Ingestion pipeline (with OCR + CV parsing)** — documents of every type ingested and structured *at ingestion time, not query time*:
   - Clean digital PDFs/text → direct parsing (`pdfplumber`)
   - Scanned/handwritten documents → local Tesseract OCR first; if confidence is low, automatically falls back to a cloud OCR API (Google Vision/AWS Textract) for higher accuracy — best of both: free for easy cases, accurate for hard ones
   - P&ID / engineering drawings → Gemini vision extracts equipment symbols, labels, and connections into graph-ready entities/relationships — no training data or specialized CV model needed
   - All three paths converge into the same entity-extraction → Neo4j-loading step, so downstream agents don't need to know or care which ingestion path a fact originally came from
   - Result: query-time latency stays low, since all the expensive parsing already happened once, upfront, per document — not repeated on every user question
2. **Real-time continuous ingestion** — a Python `watchdog` file-watcher detects new documents in a monitored folder and pushes the file path onto a **Redis + RQ** queue; a background worker (the same ingestion pipeline from #1) processes the queue asynchronously, so file-detection never blocks on heavy OCR/CV/extraction work — the graph stays current as new maintenance records/reports arrive, directly satisfying the brief's "continuously updated at the point of need" requirement
3. **Supervisor + sub-agents (LangGraph)** — correctly routes to Copilot / RCA / Compliance / Lessons Learned agents based on query intent
3. **Expert Copilot (Hybrid GraphRAG)** — Q&A with citations, using Neo4j + Qdrant + BM25 + rerank, not plain vector RAG
4. **RCA Agent** — traverses failure history + work orders → produces root-cause narrative + actionable fix, as its own dedicated reasoning chain
5. **Compliance Agent** — regulatory clause vs. procedure/equipment mapping, flags gaps, generates audit-ready evidence text
6. **Lessons Learned Agent** — cross-incident pattern detection across the full document/failure history
7. **Graph visualization** — live node/edge rendering (Neovis.js/NVL) for any query result
8. **GraphRAG vs. plain-RAG side-by-side demo** — the core differentiator (see Section 9)
9. **Knowledge-retirement-risk view** — flags knowledge tied to soon-to-retire personnel
10. **Proactive Intelligence Layer** — synthetic telemetry feed drives auto-drafted work orders and warnings, pushed to the UI before a user asks
11. **RAGAS evaluation dashboard** — live quality scoring of every Copilot/agent answer

---

## 8a. Evaluation & Quality Assurance (RAGAS)

Every answer produced by the Copilot/sub-agents is scored on:
- **Faithfulness** — does the answer only state what's actually supported by retrieved context?
- **Context precision** — how much of the retrieved context was actually relevant?
- **Answer relevancy** — does the answer actually address the question asked?

These scores are surfaced on a live dashboard panel in the UI. This directly targets the brief's evaluation focus on "query answer quality" and gives judges a *measured*, not just claimed, quality signal — a meaningful technical-excellence differentiator, since most competing teams will not have instrumented evaluation.

---

## 8b. Proactive Intelligence Layer

A synthetic telemetry generator simulates live sensor/operational signals against the synthetic plant. Each incoming telemetry reading (e.g. temperature, vibration, pressure) is treated as a numeric feature vector and compared against stored `FailureEvent` signatures using **similarity scoring** (e.g. distance-based comparison across the full combination of readings), rather than fixed per-field thresholds — this catches "close but not exact" patterns where no single reading crosses an obvious cutoff but the overall combination matches a known failure profile. When a telemetry pattern's similarity score crosses a set confidence level, the system:
1. Surfaces a proactive warning in the UI (not waiting for a user query)
2. Auto-drafts a work order pre-filled with the likely equipment, symptom, and recommended action
3. Lets the user accept/edit/reject the draft

This directly answers the brief's requirement that the platform be **"actionable," not just "queryable,"** and gives the demo an interactive, tangible moment (e.g. a telemetry slider the presenter can move live to trigger the warning-to-draft flow).

---

## 9. Key Differentiators ("Wow Factors")

Prioritized by effort-to-impact ratio:

1. **GraphRAG vs. plain-vector-RAG live comparison** (lowest effort, highest visible impact) — replicate the pattern Neo4j itself demonstrated (plain RAG conflating unrelated entities; GraphRAG correctly anchoring to the right node). Reference: NeoConverse blog post, Neo4j Labs.
2. **Answer-trail visualization** — render the actual path (Question → Chunk → Equipment → Failure → Procedure) the answer traveled through, not just footnote citations.
3. **Retirement-risk view** — directly answers the brief's own "knowledge cliff" framing; likely no other team will think of this.
4. **Proactive push** — agent flags relevant risk on ingestion of a new document, rather than only responding to queries.

**Decision needed:** Confirm which 1–2 of these ship in the final demo — see Section 12 (Open Decisions).

---

## 10. Demo Script (Target: 5 minutes)

1. Hook (30s) — cite 35% time-loss stat
2. Show fragmentation (30s) — scattered doc types
3. Ingestion → graph, live or pre-recorded (60s)
4. Ask Copilot a real RCA question — show graph-expanded answer with citations (90s)
5. Side-by-side: same question against plain vector RAG vs. our GraphRAG (60s) — the core "wow"
6. Close (30s) — reiterate business impact + mobile-first + roadmap

---

## 11. Judging Criteria Alignment

| Criteria | Weight | How addressed |
|---|---|---|
| Innovation | 25% | GraphRAG reasoning vs. plain retrieval; unified single-agent router vs. disconnected tools |
| Business Impact | 25% | Anchored to 35% time-loss / 18–22% downtime stats |
| Technical Excellence | 20% | Real graph traversal + real tool-calling, no hardcoded demo paths |
| Scalability | 15% | Same ingestion pipeline handles any doc type/volume without redesign |
| User Experience | 15% | Mobile-responsive chat UI (brief explicitly requires this) |

---

## 12. Build Order / Milestones

| Phase | Deliverable |
|---|---|
| 1 | Neo4j schema live + seed data loaded; synthetic plant fully authored, including some scanned/handwritten samples and at least one P&ID diagram |
| 2 | Full ingestion pipeline validated across all three paths (clean text, OCR, CV/P&ID) plus the continuous-ingestion watcher; entity extraction accuracy checked against manual ground truth for each path |
| 3 | Hybrid retrieval layer wired (Neo4j + Qdrant + BM25 + Cohere rerank), tested for retrieval quality before any agent consumes it |
| 4 | Each sub-agent (Copilot, RCA, Compliance, Lessons Learned) built and independently tested with domain-specific query sets |
| 5 | Supervisor/LangGraph routing tested across a broad query set spanning all four intents, including ambiguous/mixed-intent queries |
| 6 | RAGAS evaluation wired in, baseline scores established, iterate on retrieval/prompting until scores stabilize |
| 7 | Proactive telemetry layer built and connected to the graph pattern-matcher |
| 8 | Frontend fully connected (chat, graph viz, telemetry slider, RAGAS dashboard) |
| 9 | GraphRAG vs. plain-RAG comparison built and rehearsed |
| 10 | Deployment (Vercel + Railway/Render), deck, demo video, full rehearsal |

---

## 13. Open Decisions (Need Input Before / During Build)

- [ ] **LangGraph state schema** — exact shape of the state object passed between Supervisor and sub-agents (needs to be defined before any agent code is written, since all agents depend on it)
- [ ] **RAGAS thresholds** — what faithfulness/precision/relevancy scores count as "acceptable" for the dashboard, and what action (if any) the system takes when a score is low
- [ ] **Exact synthetic "plant" details** (equipment names, failure scenarios, telemetry signatures) — needs to be authored before ingestion/telemetry testing can start
- [ ] **Deployment environment** — confirm Vercel + Railway/Render vs. alternative hosting

---

## 14. Risks (Engineering Rigor, Not Time Scarcity)

| Risk | Mitigation |
|---|---|
| Retrieval inconsistency across three sources (Neo4j, Qdrant, BM25) | Test each retrieval path independently before combining; validate reranked output against known-correct answers |
| Supervisor misroutes an ambiguous/mixed-intent query | Build an explicit fallback path (generic hybrid retrieval + Copilot) for low-confidence routing, and test routing against a deliberately ambiguous query set, not just clean ones |
| Sub-agent reasoning chains drift from source data (hallucination) | RAGAS faithfulness scoring catches this quantitatively; treat low scores as a build blocker, not a footnote |
| Cross-session memory (mem0) surfaces stale or contradictory context | Define explicit memory-refresh/expiry rules rather than treating memory as permanently authoritative |
| Proactive telemetry layer produces false-positive warnings | Validate pattern-matching thresholds against the full synthetic failure history before demo, tune for precision |
| "Just another RAG chatbot" perception despite the added rigor | Make the hybrid-retrieval and RAGAS-scoring machinery *visible* in the demo (dashboard, side-by-side comparison), not just present in the backend |
| OCR/CV extraction errors on scanned docs or P&ID diagrams silently corrupt the graph | Spot-check extracted entities against source documents after ingestion; treat entity-extraction accuracy as a measured metric (Section 8a covers answer quality — extraction accuracy should be tracked the same way) |
| File-watcher/poller for continuous ingestion misses or double-processes a file | Use file hashing/checksums to detect true "new" files and avoid duplicate graph entries; log every ingestion event for auditability |

---

*Status: Draft — update as decisions in Section 13 are resolved. Flag here or in chat anytime you're stuck or unsure — better to pause and decide together than build in the wrong direction.*
