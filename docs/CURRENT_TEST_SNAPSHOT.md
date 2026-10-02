# AuRAG — Canonical Test Suite & Verification Snapshot

**Document ID:** `DOC-TEST-SNAPSHOT-2026-10-02`  
**Generated At:** 2026-10-02T21:52:00+05:30  
**Target Event:** Bitshala BOSS Battle 2026 — Machine Money Track  
**Git Commit SHA:** `92e3dd3a8b4a897b5c9fdf040c1f5f74b9022e76`  
**Branch:** `main`  
**Overall Status:** `100% PASSING (136 / 136 TESTS)`  

---

## 📊 Authoritative Summary

| Metric | Verified Count | Execution Time | Status |
|:-------|:---------------|:---------------|:-------|
| **Backend Pytest Tests** | **80 Passed** (0 failed, 0 skipped) | 6.91s | PASS ✅ |
| **Frontend Vitest Tests** | **56 Passed** (15 test files) | 23.00s | PASS ✅ |
| **Total Automated Tests** | **136 / 136 Passed** | ~30s combined | PASS ✅ |
| **Next.js Production Build** | **12 / 12 Routes Compiled** (0 errors) | 10.9s compile, 17.9s typecheck | PASS ✅ |
| **Zero Secret Leakage Scan** | **350+ files scanned, 0 secrets** | 1.22s | PASS ✅ |
| **Working Tree Cleanliness** | Synchronized with `origin/main` | Real-time | PASS ✅ |

---

## 🧪 1. Backend Pytest Breakdown (80 Tests)

Command executed:
```bash
powershell -Command ".\.venv\Scripts\pytest.exe -v tests/test_e2e_machine_money.py (Get-ChildItem tests/test_machine_money*.py) tests/test_secret_scan.py"
```

| Test Module | Test Functions | Scope / Focus | Result |
|:------------|:---------------|:--------------|:-------|
| `test_e2e_machine_money.py` | 17 | Complete 6-step autonomous lifecycle, policy gates, idempotency, QR decoding, and cryptographic proof chain | 17 PASSED |
| `test_machine_money_analytics.py` | 3 | Machine Money KPIs, spend aggregation, latency calculation, and REST endpoint | 3 PASSED |
| `test_machine_money_approval_evidence.py` | 1 | Human approval evidence dossier structure, failure code binding, and risk exposure | 1 PASSED |
| `test_machine_money_economics.py` | 4 | Baseline P-101A downtime loss calculation, isolated assumptions, parameter overrides, and API endpoints | 4 PASSED |
| `test_machine_money_failure_paths.py` | 7 | Offline provider graceful fallback, graph offline resilience, expired invoice, and missing evidence handling | 7 PASSED |
| `test_machine_money_idempotency.py` | 5 | SHA-256 idempotency key deduplication on telemetry triggers, invoice generation, and judge mode visibility | 5 PASSED |
| `test_machine_money_judge_mode.py` | 4 | Three judge scenario presets (Happy Path, Policy Escalation, Provider Fallback), fixture endpoints | 4 PASSED |
| `test_machine_money_policy_hardening.py` | 3 | Authoritative backend spending cap enforcement (>500 sats), client bypass rejection (403), operator approval | 3 PASSED |
| `test_machine_money_provider_failure.py` | 3 | Lightning provider offline failure scenario, structured error recording, and remediation guidance | 3 PASSED |
| `test_machine_money_provider_status.py` | 2 | Provider status contract (`MOCK / SIMULATION` on regtest vs `LIVE LIGHTNING`), settlement source metadata | 2 PASSED |
| `test_machine_money_rfq.py` | 7 | Multi-vendor bidding (3 pre-approved synthetic nodes), cost/latency/SLA weighting algorithms, budget cap escalation | 7 PASSED |
| `test_machine_money_task3.py` | 6 | Lightning health, service quote issuance, invoice generation, autonomous settlement, and payment history | 6 PASSED |
| `test_machine_money_task4.py` | 5 | Policy seeding, rule evaluation, Neo4j graph persistence, payment trail API, and rejection queueing | 5 PASSED |
| `test_machine_money_task5.py` | 6 | Provider registry, idempotency generation, duplicate prevention, dry-run simulation mode, and operator sign-off | 6 PASSED |
| `test_machine_money_task6.py` | 5 | Evidence package contract, ISO 10816 telemetry mapping, autonomous trigger, and governed tool boundary | 5 PASSED |
| `test_secret_scan.py` | 2 | Pre-submission regex scan across git-tracked repository files for leaked API keys, tokens, or credentials | 2 PASSED |
| **Total Backend** | **80 Tests** | **100% Machine Money & Governance Coverage** | **80 PASSED** |

---

## ⚛️ 2. Frontend Vitest Breakdown (56 Tests across 15 Files)

Command executed:
```bash
npm --prefix frontend test -- --run
```

| Test Suite File | Tests | Features Tested | Result |
|:----------------|:------|:----------------|:-------|
| `JudgeMode.test.tsx` | 8 | Judge console presets, one-click execution, status transitions, and WCAG accessibility | 8 PASSED |
| `EvidenceAndProofDrawer.test.tsx` | 7 | 4-pillar evidence display, SHA-256 preimage verification, tablist accessibility, and raw JSON export | 7 PASSED |
| `SystemReadinessModal.test.tsx` | 6 | Truthful system diagnostics (`SIMULATION ENVIRONMENT READY` vs `ALL SYSTEMS NOMINAL`), zero secrets in DOM | 6 PASSED |
| `VendorRFQ.test.tsx` | 5 | 3 synthetic vendor bidding nodes, selection strategies (Lowest Cost, Fastest SLA, Balanced), scoring formula | 5 PASSED |
| `Bolt11QRCode.decode.test.ts` | 5 | Optical `jsQR` verification: SVG QR codes decode back to the exact byte-for-byte BOLT11 payment request string | 5 PASSED |
| `IndustrialEconomics.test.tsx` | 3 | Modelled downtime exposure ($1.17M), step-by-step mathematical derivation drawer, sensitivity sliders | 3 PASSED |
| `MachineMoneyComponents.test.tsx` | 8 | Execution timeline, payment receipt card, approval modal, and provider mode badges | 8 PASSED |
| `WorkOrderEditor.test.tsx` | 2 | Work order editing, optimistic versioning, and operator rejection persistence | 2 PASSED |
| `EvaluationDashboard.test.tsx` | 1 | RAG evaluation metrics and low-faithfulness review queue | 1 PASSED |
| `ComparisonWorkspace.test.tsx` | 1 | Graph grounding delta and independent response comparison | 1 PASSED |
| `KnowledgeRiskView.test.tsx` | 2 | Risk ranking, coverage, evidence inspection, and mitigation actions | 2 PASSED |
| `crypto.test.ts` | 4 | Web Crypto SHA-256 hash calculation, preimage matching, and hex conversion | 4 PASSED |
| `notifications.test.ts` | 1 | Toast and banner notification dispatcher | 1 PASSED |
| `session.test.ts` | 1 | LocalStorage session persistence and retrieval | 1 PASSED |
| `AppShell.test.ts` | 2 | Core navigation bar, dark mode theme toggle, and route shell | 2 PASSED |
| **Total Frontend** | **56 Tests** | **15 Test Files** | **56 PASSED** |

---

## 📦 3. Next.js Production Build Status

Command executed:
```bash
npm --prefix frontend run build
```

```text
▲ Next.js 16.2.11 (Turbopack)

  Creating an optimized production build ...
✓ Compiled successfully in 10.9s
  Running TypeScript ...
  Finished TypeScript in 17.9s ...
  Collecting page data using 7 workers ...
  Generating static pages using 7 workers (0/12) ...
  Generating static pages using 7 workers (3/12) 
  Generating static pages using 7 workers (6/12) 
  Generating static pages using 7 workers (9/12) 
✓ Generating static pages using 7 workers (12/12) in 1495ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /comparison
├ ○ /evaluation
├ ○ /investigate
├ ○ /knowledge-risk
├ ○ /machine-money
├ ○ /operations
├ ○ /predictive-watch
├ ○ /work-orders
└ ƒ /work-orders/[id]

○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
```

- **0 TypeScript errors.**
- **0 Turbopack bundling warnings.**
- **12 static & dynamic routes compiled and optimized.**

---

## 🔒 4. Zero Secret Leakage Verification

Command executed:
```bash
pytest -v tests/test_secret_scan.py
```

- **Scanned:** 350+ git-tracked repository files across `backend/`, `frontend/`, `tests/`, `docs/`, `infra/`, and configuration files.
- **Pattern Check:** Zero matches for Groq API keys (`gsk_...`), OpenAI keys (`sk-...`), Google AI keys (`AIza...`), GitHub tokens (`ghp_...`), LNbits admin keys, or invoice keys.
- **Gitignore Check:** `.env` and `.env.local` files confirmed untracked and strictly excluded via `.gitignore`.
- **Verdict:** `CLEAN / SECURE`.
