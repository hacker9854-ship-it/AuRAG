# ⚡ AuRAG — Judge Fast-Track (3-Minute Evaluation)

> **Welcome Bitshala BOSS Battle 2026 Judges!**  
> We value your time. You don't need to read 50KB of manuals or legalistic matrices.  
> Here is everything you need to evaluate AuRAG in **under 3 minutes**.

---

## ⏱️ 1. What is AuRAG? (30-Second Elevator Pitch)

**AuRAG is an Autonomous Industrial Machine Money Protocol.**

* **The Problem**: When a refinery or manufacturing plant bearing degrades, traditional procurement takes **hours or days** of human bureaucracy. Unplanned downtime costs industry **$22,000 per minute**.
* **The Solution**: We give the industrial machine its **own sovereign Bitcoin Lightning wallet** (BOLT-11 / Nostr NIP-47 NWC).
* **The "Why GraphRAG?" Breakthrough**: An autonomous machine holding private keys **cannot make blind payments**. GraphRAG is NOT a search box — it is the machine's *deterministic cryptographic justification engine* (validating ISO 10816 standards, warranty contracts, and SOPs) before releasing satoshis.
* **The Result**: Sensor Anomaly Detected ➔ Graph-Proven Repair Justification ➔ Autonomous Vendor RFQ ➔ Instant Lightning Settlement in milliseconds.

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
[Sovereign Lightning Settlement (NIP-47 NWC / BOLT11)]
               │
               ▼ (Preimage eaa9f3... bound in Neo4j)
[Neo4j Operational Graph: (Payment)-[:FUNDS]->(WorkOrder)]
```

> **🛡️ Zero-Failure Hackathon Architecture (1 Single Point of Network)**:  
> High-stakes hackathon demos often fail when relying on 6 cloud services (Neo4j AuraDB + Qdrant + Redis + Groq + Gemini + Lightning) over conference WiFi.  
> AuRAG defaults to a resilient **Standalone Local Engine**: local SQLite relational storage, sub-millisecond in-memory operational graph, and offline NASA IMS condition-monitoring telemetry.  
> **Only 1 single service touches the live network: The Sovereign Bitcoin Lightning Node (LNbits Signet)**. Real sats, real cryptographic preimages, zero moving parts to fail.

---

## 🎬 2. Live Demo — 1-Click Fast Path (60 Seconds)

* 🌐 **Live Web Application**: [**au-rag.vercel.app/machine-money**](https://au-rag.vercel.app/machine-money)
* 💻 **Local URL** (if running locally): [**http://localhost:3000/machine-money**](http://localhost:3000/machine-money)

### Exactly What to Click:
1. Navigate to the **Machine Money Console** (`/machine-money`).
2. Scroll to the **Judge Mode** panel at the top.
3. Click the bright Cyan button:  
   👉 **`RUN REAL DATASET REPLAY (NASA IMS)`** *(250 sats)*
4. **Watch the live 6-stage autonomous lifecycle complete in ~7 seconds**:
   * ✅ **ANOMALY DETECTED**: NASA IMS Bearing Test Rig (5.42 mm/s outer race spall excursion).
   * ✅ **EVIDENCE MATCHED**: 94% confidence match against SOP-001 & WO-1002 in Neo4j.
   * ✅ **RFQ FEDERATED**: Evaluated 3 vendor bids; selected *Apex Diagnostics* (250 sats).
   * ✅ **INVOICE ISSUED**: Standards-compliant BOLT11 invoice generated.
   * ✅ **LIGHTNING SETTLED**: Zero-counterparty micro-settlement paid; SHA-256 preimage verified.
   * ✅ **GRAPH BOUND**: Cryptographically linked into Neo4j: `(Payment)-[:FUNDS]->(WorkOrder)`.

---

## 🔥 3. Novel Bitcoin & Lightning Innovations

Judges from the Bitcoin / Bitshala community will appreciate that this is **not** a basic LNbits API wrapper:

1. **Native Nostr NIP-47 (Nostr Wallet Connect) Engine**:
   * Sovereign client implemented with NIP-04 ECDH encrypted RPC requests over Nostr relays.
   * Autonomous command execution (`pay_invoice`, `get_balance`, `get_info`) with enforce-able daily budget caps.
   * Test: `tests/test_nwc_nip47.py` (passes 100%).
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

## 🔬 4. Empirical Data Credibility (No Synthetic Hand-Waving)

Instead of relying on fictional plant generator numbers, AuRAG's primary hero benchmark runs on the **NASA IMS Bearing Run-to-Failure Dataset** (University of Cincinnati / NASA Ames Prognostics Center of Excellence):
* **Test Rig**: 4 Rexnord ZA-2115 double-row bearings running at 2,000 RPM under 6,000 lbs radial load.
* **Sensor**: High-frequency PCB 353B33 accelerometer sampled at 20 kHz.
* **Empirical Excursion (Record 042 at 147.6h)**: 5.42 mm/s radial vibration breach exceeding ISO 10816 Zone C (4.5 mm/s) threshold with outer race BPFO harmonic spall signature.
* **Open Science Citation**: [NASA Ames PCoE Dataset Repository](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/).

---

## 🧪 5. 30-Second Verification Commands

To verify that the entire codebase is genuine, tested, and fully functional:

```bash
# 1. Verify Full Backend Pytest Suite (316 tests collected & passing)
pytest -q
# Quick collect verification:
pytest --collect-only -q  # Output: 316 tests collected

# 2. Verify Frontend Vitest Suite (61 tests across 16 suites)
cd frontend
npm test -- --run

# 3. Verify Core Machine Money, Public Data & Bitcoin Suites (30 tests)
pytest tests/test_e2e_public_data_machine_money.py tests/test_e2e_machine_money.py tests/test_nwc_nip47.py -v

# 4. Verify Clean Production Build
cd frontend
npm run build
```

**Result**: 100% Passing Tests (316 Backend Pytest + 61 Frontend Vitest = 377 Total), 0 Build Errors.

---

## 📚 Technical Deep-Dive Index (Optional Appendices)

If you wish to inspect our in-depth engineering documentation, architecture diagrams, and mathematical derivations:
* 🗺️ [Machine Money Architecture Spec](./docs/ARCHITECTURE_MACHINE_MONEY.md)
* 📜 [Verification & Audit Evidence Report](./docs/MACHINE_MONEY_VERIFICATION.md)
* 📊 [Industrial Downtime Economics Derivation](./docs/MACHINE_MONEY_ECONOMICS.md)
* 🔗 [Public Dataset Provenance Audit](./docs/PUBLIC_DATASET_PROVENANCE.md)

---

<div align="center">
  <b>Built for Bitshala BOSS Battle 2026 (Machine Money Track)</b><br/>
  <i>Engineered by Niss (@hacker9854-ship-it)</i>
</div>
