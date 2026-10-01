# AuRAG — Machine Money Verification Report

**Document ID:** `DOC-MACHINE-MONEY-VERIFY-2026-10`  
**Execution Date:** 2026-10-02  
**Target Environment:** Local Workstation (Windows 11, Node v22.17.0, Python 3.12.10)  
**Provider Default Mode:** `MOCK / SIMULATION`  
**Status:** `BASELINE_VERIFIED`  

---

## 1. Test Baseline Snapshot (Task 0.1)

### 1.1 Backend Test Suite (Pytest)
```bash
.\.venv\Scripts\pytest tests/test_machine_money_task3.py tests/test_machine_money_task4.py tests/test_machine_money_task5.py tests/test_machine_money_task6.py tests/test_e2e_machine_money.py -q
```
- **Passed:** 34
- **Failed:** 0
- **Duration:** 12.20s
- **Suites Included:**
  - `tests/test_machine_money_task3.py`: Provider abstraction, mock vs LNbits factory, base interfaces
  - `tests/test_machine_money_task4.py`: Autonomous invoice creation, quote service, settlement
  - `tests/test_machine_money_task5.py`: Bidirectional graph linking (`Payment` -> `WorkOrder`, `Payment` -> `PredictiveEvent`)
  - `tests/test_machine_money_task6.py`: Policy boundary enforcement, spending cap gating
  - `tests/test_e2e_machine_money.py`: Full end-to-end integration loop

### 1.2 Frontend Unit Suite (Vitest)
```bash
cd frontend && npm test
```
- **Test Files Passed:** 7 / 7
- **Tests Passed:** 10 / 10
- **Duration:** 39.52s
- **Suites Included:**
  - `lib/notifications.test.ts` (1 test)
  - `lib/session.test.ts` (1 test)
  - `components/comparison/ComparisonWorkspace.test.tsx` (1 test)
  - `components/knowledge-risk/KnowledgeRiskView.test.tsx` (2 tests)
  - `components/work-orders/WorkOrderEditor.test.tsx` (2 tests)
  - `components/evaluation/EvaluationDashboard.test.tsx` (1 test)
  - `components/AppShell.test.ts` (2 tests)

---

## 2. Git & Provenance Integrity (Task 0.2)

- **Branch:** `main`
- **Head Commit at Start:** `2913fc7`
- **First Tracked Commit:** `f24467e` (2026-09-26 09:15:00 +0530)
- **Detailed Findings:** Recorded in `docs/HACKATHON_ELIGIBILITY.md`.
- **Integrity Rule:** No commits backdated; all historical timestamps preserved.

---

## 3. Secret & Credential Audit (Task 0.3)

| Check | Result | Detail |
|---|---|---|
| Tracked `.env` check | PASS | `.env` is untracked and in `.gitignore` |
| `.env.example` review | PASS | Placeholders only (no live API keys) |
| `.env.machine-money.example` review | PASS | Placeholders only |
| Tracked secret scan (`AIza*`, `gsk_*`, `ghp_*`) | PASS | 0 live tokens found in git-tracked files |
| CI Safety | PASS | Default provider is `mock` — no live Lightning credentials required in CI |

---

## 4. Phase 1 Verification Results (QR Correctness + Payment Honesty)

| Milestone | Acceptance Criteria | Status | Evidence |
|---|---|---|---|
| **Standards-compliant QR** | Real SVG QR encoding exact BOLT11 payload, responsive sizing, copy button, raw fallback | PASS | `frontend/components/machine-money/Bolt11QRCode.tsx` |
| **Optical QR Decode Test** | Real QR decoder (`jsQR`) decodes SVG matrix to exact invoice string | PASS | `frontend/components/machine-money/Bolt11QRCode.decode.test.ts` (1 test passed) |
| **Provider Mode Disclosure** | Backend-derived `MOCK / SIMULATION` badge with network and balance | PASS | `frontend/components/machine-money/ProviderModeBadge.tsx` |
| **Cryptographic Preimage Proof** | `SHA-256(preimage) == payment_hash` verified via Web Crypto API | PASS | `frontend/lib/crypto.ts` & `frontend/components/machine-money/ProofVerification.tsx` |
| **Component Unit Tests** | 7 tests covering QR, Badge, and Proof verification | PASS | `frontend/components/machine-money/MachineMoneyComponents.test.tsx` |
| **Crypto Unit Tests** | 4 tests covering hex/bytes and SHA-256 test vectors | PASS | `frontend/lib/crypto.test.ts` |
| **Total Frontend Tests** | 10 test files, 22 tests passing | PASS | Vitest run: 22 passed in 12.98s |
| **Backend Regression** | 34 existing Machine Money tests | PASS | Pytest run: 34 passed in 9.28s |
