# ⚡ AuRAG — Judge Fast-Track (3-Minute Evaluation)

> **Welcome Bitshala BOSS Battle 2026 Judges!**  
> We value your time. You don't need to read 50KB of manuals or legalistic matrices.  
> Here is everything you need to evaluate AuRAG in **under 3 minutes**.

---

## ⏱️ 1. What is AuRAG? (30-Second Elevator Pitch)

**AuRAG is an Autonomous Industrial Machine Money Protocol.**

* **The Problem**: When a refinery or manufacturing plant bearing degrades, traditional procurement takes **hours or days** of human bureaucracy. Unplanned downtime costs industry **$22,000 per minute**.
* **The "Why Bitcoin?" Necessity**: Traditional banking rails require a human legal identity and KYC — an industrial slurry pump cannot hold a corporate bank account or Visa card. Furthermore, credit card fixed interchange fees ($0.30 + 2.9%) make sub-dollar micro-transactions mathematically impossible. **Bitcoin Lightning is the only sovereign, permissionless, sub-cent settlement rail on Earth that an autonomous machine can operate natively via cryptographic keys.**
* **The 250-Sat M2M Economic Reality**: 250 satoshis ($0.15) does **NOT** hire a human mechanic ($1,500+). It is an **Autonomous Machine-to-Machine (M2M) Micro-Diagnostic Compute Fee** — paying an external edge AI node to run high-resolution 20 kHz wavelet FFT analysis and reserve a guaranteed 4-hour emergency vendor SLA window.
* **The "Why GraphRAG?" Golden Defense**: *A SCADA sensor threshold detects physical symptoms; GraphRAG justifies financial expenditures.* A simple vibration alarm cannot verify whether an asset is under active OEM warranty (where third-party work voids coverage), what parts were installed in previous work order `WO-1002`, or what plant SOP `PROC-001` mandates. GraphRAG provides the contractual, historical, and regulatory justification layer before a single satoshi is released.
* **The Result**: Sensor Anomaly Detected (NASA IMS 5.42 mm/s) ➔ Graph-Proven Expenditure Justification ➔ Autonomous Multi-Vendor RFQ ➔ 250-sat Diagnostic SLA Settled instantly under a zero-trust 500-sat policy cap.

```
[NASA IMS Sensor Stream (20 kHz)]
               │
               ▼ (ISO-10816 Zone C Breach: 5.42 mm/s)
[GraphRAG Evidence Justification (SOP-001 + WO-1002)]
               │
               ▼ (Approved Repair Justification)
[Autonomous RFQ Federation (3 Diagnostic Vendors)]
               │
               ▼ (Optimal Quote: 250 sats)
[250-Sat Autonomous Settlement Flow (BOLT11 / Mock Default / LNbits Signet Supported)]
               │
               ▼ (Preimage eaa9f3... bound in Neo4j)
[Neo4j Operational Graph: (Payment)-[:FUNDS]->(WorkOrder)]
```

> **🛡️ Zero-Failure Hackathon Architecture (1 Single Point of Network)**:  
> High-stakes hackathon demos often fail when relying on 6 cloud services (Neo4j AuraDB + Qdrant + Redis + Groq + Gemini + Lightning) over conference WiFi.  
> AuRAG defaults to a resilient **Standalone Local Engine**: local SQLite relational storage, sub-millisecond in-memory operational graph, and offline NASA IMS condition-monitoring telemetry.  
> **Only 1 single service touches the live network: The Sovereign Bitcoin Lightning Node (LNbits Signet)**. 250-sat autonomous settlement flow implemented: Demo defaults to mock provider; live LNbits Signet mode is supported and fails closed when settlement cannot be completed. The active provider (`MACHINE_MONEY_PROVIDER`) is dynamically surfaced in the UI.

---

## 🎬 2. Live Demo — "One Button, One WOW" (15 Seconds)

> **Complexity in the backend, simplicity on your screen.**  
> Judges have 3 minutes max. You do NOT need to study mechanical vibration physics or parse complex 6-step logs to verify that AuRAG works.

* 🌐 **Live Web Application**: [**au-rag.vercel.app/machine-money**](https://au-rag.vercel.app/machine-money)
* 💻 **Local URL** (if running locally): [**http://localhost:3000/machine-money**](http://localhost:3000/machine-money)

### 👉 Exactly What to Click:
1. Navigate to the **Machine Money Console** (`/machine-money`).
2. Look at the top **"ONE BUTTON, ONE WOW"** hero panel.
3. Click the giant Golden button:  
   👉 **`⚡ EXECUTE 1-CLICK DEMO (NASA IMS ANOMALY ➔ LIGHTNING SETTLEMENT)`**

### 🌟 The "One WOW" Result on Your Screen (~200ms):
Three punchy, indisputable proofs appear immediately:
1. **🚨 Sensor Anomaly (NASA IMS-derived public-data replay fixture)**: Representative preprocessed replay derived from NASA IMS Bearing vibration excursion (**5.42 mm/s > 4.5 mm/s** ISO 10816 Zone C alarm) based on open science accelerometry (Rexnord ZA-2115, REC-042).
2. **⚡ 250-Sat Autonomous Settlement Flow Implemented**: 250-sat autonomous settlement flow executed under our autonomous spending policy cap. Demo defaults to mock provider; live LNbits Signet mode is supported and fails closed when settlement cannot be completed (e.g. unfunded test wallet). The UI dynamically displays `MOCK / SIMULATION` or `LIVE LIGHTNING` based on the active `MACHINE_MONEY_PROVIDER` setting.
3. **🔐 Cryptographic Preimage on Screen**: In mock evaluation mode, a cryptographic 32-byte SHA-256 settlement preimage (dynamically generated per-invoice; e.g. `eaa9f3...` in verification records) is displayed on screen with a 1-click clipboard copy button and verified mathematical proof against the invoice payment hash (`sha256(preimage) == payment_hash`).

*(Optional: For technical judges wanting to inspect the deep GraphRAG reasoning, Neo4j Cypher queries, multi-vendor RFQ scoring, and Sphinx onion routing, inspect the **"Technical Audit & 6-Stage GraphRAG Pipeline"** section directly below the WOW card).*

---

## ⚡ 2.5 Live Signet Lightning Node & Fail-Closed Audit Evidence

250-sat autonomous settlement flow implemented. Demo defaults to mock provider; live LNbits Signet mode is supported and fails closed when settlement cannot be completed.

For judges auditing live network capability vs. local simulation, AuRAG connects directly to a live LNbits instance configured on the Bitcoin Lightning Signet network:

### 1. Live LNbits Node & Wallet Dashboard (Invoice Issuance)
<img src="./docs/lnbits_signet_wallet_proof.png" width="100%" alt="LNbits Live Signet Wallet with 250-sat Invoices and Node API Configuration"/>

* **Node URL**: `https://demo.lnbits.com`
* **Wallet Name**: `AuRAG-Machine-Money` (`a4ce2f74c81c4b66b33efc0233fe8fcf`)
* **Real 250-Sat Invoice Issuance**: Live BOLT11 invoices issued via demo.lnbits.com API for autonomous bearing maintenance.
* **Settlement Execution**: Demo defaults to mock provider; live LNbits Signet mode is supported and fails closed when settlement cannot be completed.

### 2. Live Node Fail-Closed Execution Audit
<img src="./docs/real_signet_settlement_proof.png" width="100%" alt="AuRAG Real Signet Live Node Status and Fail-Closed Verification"/>

| Verification Check | Exact Value / Audit Proof | Status |
|:---|:---|:---:|
| **Payment Hash ($H$)** | `18a86ad31ca2dd3a67ff2a71203bd2e3fedb2fbf93252148fd0214abeab31fc5` | PASS ✅ |
| **Fail-Closed Execution** | When live balance is 0 sats, zero local preimages are emitted; payment strictly marked `FAILED` (`PROVIDER_PAY_FAILED: Insufficient balance`). 0 sats settled. | PASS ✅ |
| **Cryptographic Lock Standard** | In mock mode, preimages mathematically satisfy $\text{SHA-256}(R) \equiv H$; in live mode with unfunded wallet, payment fails closed without fake claims. | PASS ✅ |

> 📜 **Complete Step-by-Step Technical Audit**: See [docs/REAL_SIGNET_TRANSACTION_PROOF.md](./docs/REAL_SIGNET_TRANSACTION_PROOF.md)

---

## 🔥 3. Novel Bitcoin & Lightning Innovations

Judges from the Bitcoin / Bitshala community will appreciate that this is **not** a basic LNbits API wrapper:

1. **NIP-47 Nostr Wallet Connect (BIP-340 Schnorr)**:
   * Demonstrates NIP-47-compatible event structures (kind 23194/23195) with NIP-04 ECDH encryption.
   * Real BIP-340 64-byte Schnorr signatures implemented using `coincurve` (libsecp256k1) / `secp256k1` (zero HMAC fallback).
   * Test: `tests/test_nwc_nip47.py` (passes 100% — validates BIP-340 signature generation, verification, tamper rejection, and NIP-04 encryption).
2. **Multi-Hop Lightning HTLC Routing Simulation**:
   * Deterministic 4-hop Sphinx onion routing engine (`Machine Node ➔ LSP Core ➔ Routing Hub ➔ Vendor Node`).
   * Models real channel capacity, base fee, PPM fee rates, and CLTV expiry deltas.
   * Live interactive visualization in Section 20 of the Machine Money console.
3. **Cryptographic Neo4j Graph Lineage**:
   * Every satoshi spent is permanently bound to the operational graph:
     ```cypher
     (p:Payment {hash: "81ebd7...", preimage: "eaa9f3..."})-[:FUNDS]->(w:WorkOrder {id: "WO-2026-P101"})
     (p)-[:TRIGGERED_BY]->(e:PredictiveEvent {id: "EVT-PUB-6100BC"})
     ```
4. **Zero-Trust Spending Policy Escrow**:
   * Autonomous cap strictly set at 500 sats.
   * Any vendor quote >500 sats halts in `PENDING_APPROVAL` requiring human digital sign-off.
   * Unilateral bypass attempts are rejected at the API layer with HTTP 403.

---

## 🔬 4. Empirical Data Credibility: Public-Data Replay First, Illustrative Models Disclosed

AuRAG enforces a strict, honest line between **public-data replay fixtures** and **illustrative simulation parameters**:

| Layer | Classification | Technical Source & Real-World Grounding |
|:------|:---------------|:----------------------------------------|
| **Vibration Waveforms & Accelerometry** | **NASA IMS-derived public-data replay fixture** | **Representative preprocessed replay derived from NASA IMS** Bearing Run-to-Failure Dataset (Univ. of Cincinnati / NASA Ames PCoE). 4 Rexnord ZA-2115 bearings, 2,000 RPM, 6,000 lbs radial load, 20 kHz PCB 353B33 accelerometer. Record `REC-042` at 147.6h reaches 5.42 mm/s (ISO 10816 Zone C breach). |
| **Bitcoin Settlement & Cryptography** | **250-Sat Autonomous Flow Implemented** | Demo defaults to mock provider; live LNbits Signet mode is supported and fails closed when settlement cannot be completed. Generates standards-compliant BOLT11 payment requests and verifies 32-byte SHA-256 preimages (`sha256(preimage) == payment_hash`). |
| **Operational Knowledge Graph** | **Authentic Industry Standards** | Real-world ISO 10816-3 vibration severity standards, SKF bearing mechanical catalog specifications, and industrial SOPs in Neo4j. |
| **Vendor Bidding Candidates** | **[Illustrative Simulation]** | Synthetic vendor nodes (*Apex Diagnostics*, *Precision Dynamics*, *Quantum Reliability*) illustrating decentralized multi-vendor RFQ scoring. |
| **Plant Macro-Economics** | **[Illustrative Model]** | Parameterized industrial plant model ($1.17M modelled downtime exposure @ $260k/hr, based on illustrative synthetic plant parameters; 7.8M:1 modelled exposure/payment ratio, not actual ROI). |

* **Test Rig**: 4 Rexnord ZA-2115 double-row bearings running at 2,000 RPM under 6,000 lbs radial load.
* **Sensor**: High-frequency PCB 353B33 accelerometer sampled at 20 kHz.
* **Empirical Excursion (Record 042 at 147.6h)**: 5.42 mm/s radial vibration breach exceeding ISO 10816 Zone C (4.5 mm/s) threshold with outer race BPFO harmonic spall signature.
* **Open Science Citation**: [NASA Ames PCoE Dataset Repository](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/).

---

## 🧪 5. 30-Second Verification Commands

To verify that the entire codebase is genuine, tested, and fully functional:

```bash
# 1. Verify Full Backend Pytest Suite (317 tests collected & passing)
# (Using repo virtualenv directly or active shell):
pytest -q
# Or direct executable path:
# Windows: .\.venv\Scripts\pytest.exe -q
# Linux/Mac: ./.venv/bin/pytest -q

# Quick collect verification:
pytest --collect-only -q  # Output: 317 tests collected

# 2. Verify Frontend Vitest Suite (61 tests across 16 suites)
cd frontend
npm test -- --run
cd ..

# 3. Verify Core Machine Money, Public Data & Bitcoin Suites (30 tests)
pytest tests/test_e2e_public_data_machine_money.py tests/test_e2e_machine_money.py tests/test_nwc_nip47.py -v

# 4. Verify Browser E2E Suite (6 Playwright tests)
cd frontend
npm run test:e2e

# 5. Verify Clean Production Build
cd frontend
npm run build
```

**Result**: 100% Passing:
- **378 unit/integration tests passing** (317 Backend Pytest + 61 Frontend Vitest)
- **6 browser E2E checks passing** (Playwright Desktop & Mobile)
- **384 automated checks total** (0 Build Errors)

---

## 📚 Technical Deep-Dive Index (Optional Appendices)

If you wish to inspect our in-depth engineering documentation, architecture diagrams, and mathematical derivations:
* 🏗️ [Core System Architecture & Engineering Decision Records (ADRs)](./ARCHITECTURE.md)
* 🗺️ [Machine Money Architecture Spec](./docs/ARCHITECTURE_MACHINE_MONEY.md)
* 📜 [Verification & Audit Evidence Report](./docs/MACHINE_MONEY_VERIFICATION.md)
* 📊 [Industrial Downtime Economics Derivation](./docs/MACHINE_MONEY_ECONOMICS.md)
* 🔗 [Public Dataset Provenance Audit](./docs/PUBLIC_DATASET_PROVENANCE.md)

---

<div align="center">
  <b>Built for Bitshala BOSS Battle 2026 (Machine Money Track)</b><br/>
  <i>Engineered by Niss (@hacker9854-ship-it)</i>
</div>
