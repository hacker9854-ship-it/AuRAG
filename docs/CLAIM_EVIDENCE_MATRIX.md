# AuRAG — Claim-to-Evidence Verification Matrix
**Authoritative Claims Audit for Bitshala BOSS Battle 2026**

- **Document ID:** `DOC-CLAIM-MATRIX-2026-10-02`
- **Audit Date:** 2026-10-02
- **Rule Compliance:** Non-negotiable truthfulness rule (Section 0.1 of `AuRAG_FINAL_PRD.md`)
- **Scope:** Every material technical claim in `README.md`, UI, and demo documentation mapped to exact files, automated tests, environment scope, and permitted wording.

---

## 🛡️ Master Claim-to-Evidence Matrix

| Claim | Evidence File(s) | Evidence Test(s) | Current Environment Scope | Permitted Wording | Prohibited / Overstated Wording |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BOLT11 Invoice Validity** | `backend/app/services/machine_money/bolt11.py`<br/>`backend/app/services/machine_money/providers/mock.py` | `tests/test_bolt11.py::test_bolt11_encode_decode_roundtrip`<br/>`tests/test_bolt11.py::test_mock_lightning_provider_creates_genuinely_valid_invoice` | Local mock simulation & regtest network | *"Standards-compliant, BIP-173 Bech32 and BOLT #11 valid test invoice"* | ❌ *"Live mainnet Bitcoin invoice with real value"* |
| **Optical QR Decoding** | `frontend/components/machine-money/Bolt11QRCode.tsx`<br/>`frontend/components/machine-money/Bolt11QRCode.decode.test.ts` | `frontend/components/machine-money/Bolt11QRCode.decode.test.ts` (5 tests) | Browser DOM & optical canvas matrix via `jsQR` | *"Standard SVG QR matrix optically decodable by standard Lightning scanners"* | ❌ *"Proprietary computer vision matrix"* |
| **Settlement Honesty** | `backend/app/services/machine_money/providers/mock.py`<br/>`frontend/components/machine-money/ProviderModeBadge.tsx` | `tests/test_machine_money_provider_status.py`<br/>`tests/test_e2e_machine_money.py::test_e2e_01` | MOCK / SIMULATION mode on regtest | *"MOCK / SIMULATION settlement provider for zero-risk local and CI testing"* | ❌ *"Mainnet Lightning node routing real Bitcoin"* |
| **Cryptographic Proof Chain** | `frontend/lib/crypto.ts`<br/>`backend/app/services/machine_money/service.py` | `tests/test_e2e_machine_money.py::test_e2e_17`<br/>`frontend/lib/crypto.test.ts` (4 tests) | Web Crypto API SHA-256 in browser + Python `hashlib` | *"Simulation integrity verified: SHA-256(preimage) matches payment_hash"* | ❌ *"Unforgeable blockchain finality on mock transactions"* |
| **Multi-Vendor RFQ Selection** | `backend/app/services/machine_money/rfq.py`<br/>`frontend/components/machine-money/VendorRFQ.tsx` | `tests/test_machine_money_rfq.py` (7 tests)<br/>`frontend/components/machine-money/VendorRFQ.test.tsx` (5 tests) | 3 pre-approved synthetic vendor nodes | *"Synthetic 3-vendor RFQ bidding with deterministic multi-criteria scoring"* | ❌ *"Real-time open market vendor APIs connected to live contractors"* |
| **Policy Spending Guard** | `backend/app/services/machine_money/service.py`<br/>`backend/app/services/automation.py` | `tests/test_machine_money_policy_hardening.py` (3 tests)<br/>`tests/test_e2e_machine_money.py::test_e2e_06` | Server-side policy engine | *"Strict spending policy cap (500 sats); quotes > 500 sats require operator sign-off"* | ❌ *"Zero-trust unhackable hardware enforcer"* |
| **Deterministic Idempotency** | `backend/app/services/machine_money/registry.py`<br/>`backend/app/services/machine_money/service.py` | `tests/test_machine_money_idempotency.py` (5 tests)<br/>`tests/test_e2e_machine_money.py::test_e2e_08` | SQLite / PostgreSQL session transaction lock | *"Deterministic SHA-256 idempotency key prevents duplicate charges from sensor replays"* | ❌ *"Infinite distributed idempotency guarantees without storage"* |
| **Causal Graph Lineage** | `backend/app/services/machine_money/graph.py`<br/>`backend/app/core/neo4j.py` | `tests/test_machine_money_task4.py::test_neo4j_graph_persistence_and_trail`<br/>`tests/test_e2e_machine_money.py::test_e2e_02` | Neo4j Cypher operational knowledge graph | *"Cryptographic binding linking (Payment)-[:FUNDS]->(WorkOrder) & (PredictiveEvent)"* | ❌ *"Automatic graph self-healing agent"* |
| **Industrial Economics Model** | `backend/app/services/machine_money/economics.py`<br/>`frontend/components/machine-money/IndustrialEconomics.tsx` | `tests/test_machine_money_economics.py` (4 tests)<br/>`frontend/components/machine-money/IndustrialEconomics.test.tsx` (3 tests) | Parameterized synthetic plant model (4.5h @ $260k/hr) | *"$1.17M modelled downtime exposure; 7,800,000:1 modelled exposure-to-cost multiple"* | ❌ *"$1.17M empirical cash saved in bank accounts"* |
| **Provider Failure Resilience** | `backend/app/services/machine_money/service.py`<br/>`backend/app/services/machine_money/providers/mock.py` | `tests/test_machine_money_provider_failure.py` (3 tests)<br/>`tests/test_e2e_machine_money.py::test_e2e_15` | Simulated channel liquidity exhaustion | *"0 sats deducted on routing failure; structured error and remediation guidance logged"* | ❌ *"100% SLA uninterrupted routing guarantee"* |
| **Zero Secret Exposure** | `.gitignore`<br/>`.env.example`<br/>`tests/test_secret_scan.py` | `tests/test_secret_scan.py` (2 tests) | Git-tracked file scanner | *"No credentials, private keys, or tokens exposed in repository source code"* | ❌ *"Fully air-gapped hardened hardware security module"* |
| **System Readiness Diagnostics** | `backend/app/services/machine_money/service.py`<br/>`frontend/components/machine-money/SystemReadinessModal.tsx` | `frontend/components/machine-money/SystemReadinessModal.test.tsx` (6 tests) | Server-reported health endpoints | *"Truthful environment diagnostics reflecting real connected services or unconfigured fallbacks"* | ❌ *"All systems nominal when services are disconnected"* |
| **Sub-Second Execution Speed** | Execution stage timers in `service.py` | `tests/test_machine_money_task3.py`<br/>`tests/test_e2e_machine_money.py` | Measured local runtime latency | *"Measured demo execution time of 150-350ms in local test environments"* | ❌ *"Global Bitcoin network propagation under 1 millisecond"* |

---

## 🔍 Audit Verification Method

Each row in this matrix was independently verified against:
1. **Source Code:** Inspection of function definitions and docstrings in `backend/app` and `frontend/components`.
2. **Automated Tests:** Execution via `pytest` (85 tests) and `vitest` (56 tests).
3. **Documentation:** Regular expression audits of `README.md`, `PRD3.md`, and `AuRAG_FINAL_PRD.md` to ensure prohibited terms are absent.

**Audit Sign-Off:** All 13 core claims comply with Section 0.1 (Truthfulness) rules.
