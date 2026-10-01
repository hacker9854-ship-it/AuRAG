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

## 4. Known Issues & Remediation Target for Next Phases

1. **Pseudo-Grid QR (Phase 1 Target):** Current `Bolt11QRCode` in `frontend/app/machine-money/page.tsx` renders a synthetic pattern instead of a standards-compliant matrix. Will be replaced in Phase 1 with a real encoder.
2. **Provider Mode Visual Clarity (Phase 1 Target):** Ensure prominent `MOCK / SIMULATION` label is visible across all payment views.
3. **Cryptographic Proof Utility (Phase 1 Target):** Expose deterministic `SHA256(preimage) == payment_hash` verification.
