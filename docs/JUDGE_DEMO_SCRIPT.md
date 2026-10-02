# AuRAG — Machine Money Judge Demo Script (3–5 Minutes)

**Target Track:** Bitshala BOSS Battle 2026 — Machine Money Track ($1,000 Prize Pool)  
**Speaker:** Lead Builder (Niss)  
**Live Demo URL:** [https://au-rag.vercel.app/machine-money](https://au-rag.vercel.app/machine-money)  
**Backend API:** [https://aurag-production.up.railway.app](https://aurag-production.up.railway.app)  
**Target Duration:** 4 to 5 minutes  

---

## ⏱️ Minute-by-Minute Narration & Screen Guide

### 🎬 Part 1: The Core Problem (0:00 – 0:20)
* **Screen:** Open [`https://au-rag.vercel.app/machine-money`](https://au-rag.vercel.app/machine-money) displaying the top Judge Orientation Ribbon.
* **Narration:**
  > "Judges, modern industrial IoT is filled with sensors that detect critical anomalies in milliseconds. But what happens next? 
  > Action stops. Work orders sit in disconnected ERP queues, vendor dispatch takes days of manual invoicing, and plants suffer catastrophic unplanned downtime.
  > Today, we present **AuRAG Machine Money** — the first autonomous machine-to-machine payment protocol that binds **physical industrial telemetry**, **deterministic GraphRAG evidence**, **automated spending governance**, and **instant Bitcoin Lightning micro-settlement** into a single closed loop."

---

### 🔍 Part 2: The Graph & Evidence Layer (0:20 – 0:50)
* **Screen:** Point cursor to the **5-Question Judge Orientation Ribbon** (`1. Why We Pay`, `2. Justified By`, `3. Why Allowed`, `4. Settlement`, `5. Business Impact`) and the **Evidence Summary Card**.
* **Narration:**
  > "Before a single satoshi moves, a machine must prove *why* it is paying. 
  > Notice our above-the-fold Judge Orientation ribbon:
  > In AuRAG, Crude Charge Pump **P-101A** experienced an ISO 10816 Zone C radial vibration excursion reaching 5.8 mm/s against a 4.5 mm/s limit.
  > Our hybrid GraphRAG engine instantly correlated this vibration spectrogram with historical failure signature **FE-001** and maintenance standard **PROC-001** with 94% confidence.
  > Machine Money never hallucinates or pays blindly — financial settlement is strictly grounded in immutable operational evidence."

---

### ⚡ Part 3: One-Click "Run Industrial Emergency" (0:50 – 2:10)
* **Screen:** Click the golden **`▶ RUN INDUSTRIAL EMERGENCY`** button in the Judge Mode console.
* **Narration:**
  > "Let's run the end-to-end autonomous pipeline right now with one click.
  > Watch the live **Execution Timeline**:
  > 1. **Telemetry Detected:** Sensor excursion confirmed at 12ms.
  > 2. **Evidence Matched:** Graph ontology binds failure signature FE-001.
  > 3. **Autonomous RFQ Resolved:** 3 pre-approved synthetic vendor nodes bid; the algorithm selects the optimal SLA provider for 250 sats.
  > 4. **Policy Evaluated:** 250 sats is within our plant automated cap of 500 sats. Approved.
  > 5. **Invoice Generated:** Real BOLT11 payment request synthesized.
  > 6. **Payment Authorized & Settled:** Micro-payment settled via Lightning adapter in under 200ms.
  > 7. **Graph Linked & Outcome Resolved:** Preimage committed to Neo4j knowledge graph and SQL audit ledger."

---

### 🔐 Part 4: Spending Policy & Cryptographic Proof (2:10 – 2:50)
* **Screen:** Click **"Inspect Verifiable Proof Package"** or the **Proof** button on the settled payment row. Open the **Payment Proof Drawer**.
* **Narration:**
  > "Now let's examine the cryptographic honesty.
  > Notice the badge at the top: **MOCK / SIMULATION** on `regtest`. We believe in 100% technical honesty — deterministic simulation ensures zero risk of live fund loss in judging environments.
  > On Tab 1, we see our **SHA-256 Preimage Verification** powered by the Web Crypto API. The 32-byte secret preimage hashes directly to the payment hash: `SHA256(preimage) == r_hash`. It is mathematically unforgeable.
  > On Tab 2, we have the **Standards-Compliant BOLT11 QR Code**. This is not a static graphic — it is a live SVG matrix encoding the exact invoice string, independently verified by optical `jsQR` decoder tests."

---

### 📊 Part 5: Neo4j Lineage & Industrial Economics (2:50 – 3:30)
* **Screen:** Switch to **Tab 3: Operational Graph Lineage**, then close the drawer and scroll down to the **Industrial Economics** dashboard.
* **Narration:**
  > "On Tab 3, notice our 6-node Neo4j semantic trail:
  > `(Equipment: P-101A) -> (PredictiveEvent) -> (FailureSignature: FE-001) -> (WorkOrder: WO-1002) -> (Payment) -> (ServiceProvider)`.
  > Auditing is bidirectional — you can start from a satoshi transaction and trace back to the physical motor bearing.
  > Now look at the bottom dashboard: **Industrial Economics**.
  > Why spend 250 sats? Because pump P-101A carries an hourly outage loss of $260,000. 
  > A 250-sat intervention ($0.16) averts 4.5 hours of emergency downtime, preserving **$1.17M in gross exposure** — an economic protection multiple of **7.2 Million to 1**!
  > Every assumption is transparently parameterized in our Explainability Drawer."

---

### 🛡️ Part 6: Human-in-the-Loop Escalation (>500 Sats) (3:30 – 4:00)
* **Screen:** Scroll up to Judge Mode and click **`Run Policy Escalation (>500 sats)`**.
* **Narration:**
  > "What happens if a rogue agent or catastrophic repair quotes 1,200 sats?
  > Let's test it: 1,200 sats exceeds our 500-sat autonomous cap.
  > Watch the system halt: the backend policy engine unconditionally holds the transaction in **`PENDING_APPROVAL`**.
  > Even if a malicious client sends `bypass_policy: true`, our authoritative backend rejects unilateral bypass with HTTP 403 Forbidden.
  > The plant operator receives an enriched evidence dossier with sensor spectrograms and downtime risk before digital sign-off."

---

### 🏆 Part 7: Architecture Summary & Defensibility (4:00 – 5:00)
* **Screen:** Click the **`System Readiness`** badge in the header strip to display the 6 nominal subsystems.
* **Narration:**
  > "To summarize our technical defensibility:
  > 1. **Zero Credential Leaks:** Our pre-submission scanners scanned 350+ files — zero API keys or secrets in source.
  > 2. **Complete Test Coverage:** 77 Pytest backend tests and 52 Vitest frontend tests — 100% green across regression, failure-paths, and E2E loops.
  > 3. **Production Deployed:** Next.js 16 live on Vercel, FastAPI Docker container live on Railway.
  > 4. **Authentic Provenance:** All code written during the Bitshala build window with preserved git timestamps.
  > AuRAG proves that when machines have money, industrial operations transform from slow, reactive maintenance into autonomous, self-healing cyber-physical infrastructure.
  > Thank you, and we welcome your questions!"

---

## 📋 Judge Q&A Cheat Sheet

| Question | Short Answer | Deep Technical Proof |
|---|---|---|
| *Is this real Bitcoin Lightning?* | By default, it runs in **MOCK / SIMULATION** mode for safety, but with a pluggable adapter. | `LNbitsProvider` in `lnbits.py` supports real LNbits wallets. Mock provider generates cryptographically sound BOLT11 invoices and 32-byte preimages verified via Web Crypto SHA-256. |
| *Can an agent spend unlimited funds?* | Absolutely not. The backend spending cap is authoritative. | Hardened in `service.py`: any transaction > 500 sats unconditionally enforces `PENDING_APPROVAL`. Client cannot bypass via API. |
| *What happens if the Lightning node goes down?* | Deterministic failure state with zero loss. | Tested in `test_machine_money_provider_failure.py`: status marks `FAILED`, 0 sats debited, `AuditEvent` logs channel rebalancing retry guidance. |
| *What prevents duplicate payments?* | Deterministic SHA-256 idempotency key. | `idemp-sha256(site:asset:svc:evt)` prevents duplicate processing; re-sent triggers return existing record with `is_duplicate_prevented: True`. |
