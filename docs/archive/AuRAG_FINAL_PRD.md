# PRD — AuRAG Final Hackathon Hardening & Submission Plan
**Master Phased Execution Document**

- **Project:** AuRAG — Autonomous Industrial Intelligence + Machine Money
- **Track:** Machine Money (Bitshala BOSS Battle 2026)
- **Target:** 100% Truthful, Judge-Defensible, Production-Structured Submission
- **Execution Style:** Phase-gated, test-driven, MCP browser-verified, commit-after-green

---

## 0. Master Execution Protocol for AI Agent

### 0.1 One-Command Phase Execution
The user will command one phase at a time using simple prompts:
- `phase 2 start kro`
- `phase 3 start kro`
- `phase X start kro`

When a phase command is received, the agent must autonomously:
1. **Locate Phase Specification**: Read the exact tasks, target files, acceptance criteria, and commit message from Section 3.
2. **Inspect Current Code**: Check the actual workspace files before modifying.
3. **Implement**: Apply the required backend, frontend, schema, or documentation changes.
4. **End-to-End Test Suite**:
   - Backend: Run full `pytest` suite (`.\.venv\Scripts\pytest.exe -v ...`).
   - Frontend: Run full `vitest` suite (`npm --prefix frontend test -- --run`).
   - Build: Run Next.js production build (`npm --prefix frontend run build`).
   - Browser / UI: Use Chrome DevTools MCP or browser subagent to visually verify changes and ensure zero console errors.
5. **Fix Any Bugs**: Iterate until 100% of tests pass and build succeeds. Zero test skipping or silencing allowed.
6. **Commit & Push to GitHub**: Commit using the exact conventional commit message specified for the phase, and run `git push origin main`.
7. **Report & Wait**: Present a concise status report with modified files, test outputs, and commit hash, then wait for the user's next command.

### 0.2 Definition of Done (DoD)
A phase is considered **DONE** only when:
- [x] All task acceptance criteria for that phase are satisfied.
- [x] Backend tests pass (85+ Pytest).
- [x] Frontend tests pass (56+ Vitest).
- [x] Next.js production build passes with 0 TypeScript/ESLint errors.
- [x] Visual verification via browser tools/screenshots confirms expected UI behavior.
- [x] Zero secrets or private keys exposed in code or git.
- [x] Mock vs. Live behavior is truthfully labeled across UI, API, and docs.
- [x] Changes committed and pushed to `origin/main`.

### 0.3 Non-Negotiable Truthfulness & Provenance Rules
- **No History Manipulation**: Never use `git filter-branch`, `filter-repo`, or fake commit timestamps to fabricate development timelines. Commit timestamps must reflect real-world execution.
- **Explicit Simulation Disclosure**: All synthetic data, simulated preimages, regtest invoices, and mock providers must be clearly labeled `MOCK / SIMULATION`. Never masquerade simulated payments as real mainnet Bitcoin transactions.
- **Modelled Economic Estimates**: Downtime calculations ($1.17M exposure on P-101A) must be explicitly disclosed as **Modelled Estimates based on synthetic plant parameters**, not empirical historical losses.
- **Standards Validity**: If claiming BOLT11, the invoice must parse under standard BIP-173 Bech32 and BOLT #11 decoders. (Completed in Phase 1).

---

## 1. Canonical Scenario & System Parameters

Use one canonical judge scenario across all documentation, UI, fixtures, and tests:

| Parameter | Canonical Value | Meaning / Disclosure |
| :--- | :--- | :--- |
| **Equipment ID** | `P-101A` | Centrifugal Slurry Pump |
| **Sensor ID** | `VIB-301-BEARING` | High-frequency vibration accelerometer |
| **Vibration Reading** | `5.4 mm/s` | Current anomalous reading |
| **ISO Threshold** | `4.5 mm/s` | ISO 10816-3 Warning Threshold |
| **Service ID** | `bearing-inspection` | Emergency autonomous inspection dispatch |
| **Autonomous Spend** | `250 sats` | Micro-payment for service dispatch |
| **Autonomous Cap** | `500 sats` | Hard limit for autonomous execution |
| **Escalation Spend** | `1,200 sats` | Motor rewind overhaul (> 500 sats cap) |
| **Vendors** | `3` | Apex Diagnostics, Precision Dynamics, Quantum Reliability |
| **Vendor Type** | `Synthetic` | Pre-approved vendor nodes in demonstration |
| **Evidence ID** | `FE-001` | Bearing outer-race spalling defect |
| **Work Order ID** | `WO-1002` | Historical overhaul report |
| **Procedure ID** | `PROC-001` | Lubrication & bearing inspection SOP |
| **Modelled Downtime** | `4.5 hours` | Modelled avoided outage duration |
| **Hourly Rate** | `$260,000 / hr` | Modelled plant downtime exposure rate |
| **Modelled Exposure** | `$1.17M` | Total potential financial loss mitigated |
| **Protection Multiple** | `7,800,000:1` | Modelled ratio of exposure mitigated to intervention cost |

---

## 2. Master Phase Roadmap & Live Execution Tracker

| Phase | Title | Scope & Deliverable | Status | Commit / Target |
| :---: | :---|:---|:---:|:---|
| **Phase 0** | Baseline Freeze & Evidence Matrix | Test snapshot, 103 verified links, 13-row claim evidence matrix | **[COMPLETED]** | [`0609a97`](https://github.com/hacker9854-ship-it/AuRAG/commit/0609a97), [`c8a4ad3`](https://github.com/hacker9854-ship-it/AuRAG/commit/c8a4ad3) |
| **Phase 1** | Protocol-Sound BOLT11 Invoices | Pure Python BIP-173 Bech32 + secp256k1 compact ECDSA encoder/decoder; mock provider emits parseable BOLT11 | **[COMPLETED]** | [`25b6adf`](https://github.com/hacker9854-ship-it/AuRAG/commit/25b6adf) |
| **Phase 2** | Ground Judge Mode in Actual Retrieval | Wire `retrieval.hybrid.retrieve` in `grounding.py` for evidence matching, with explicit `CONTROLLED DEMO FIXTURE` fallback | **[READY TO EXECUTE]** | `feat(machine-money): ground judge mode in hybrid graph retrieval` |
| **Phase 3** | Causal Payment Evidence Chain & Proof Drawer | 6-tab proof drawer (Why We Paid, RFQ Decision, Policy Decision, Lightning Proof, Graph Lineage, Audit Ledger) | **[READY TO EXECUTE]** | `feat(machine-money): strengthen causal payment evidence chain` |
| **Phase 4** | Finalize Deterministic Judge Scenarios & Reset | Standardize 3 scenarios (A: Autonomous 250 sats, B: Escalation 1200 sats, C: Provider Failure) with total state `RESET DEMO` | **[READY TO EXECUTE]** | `feat(machine-money): finalize deterministic judge scenarios` |
| **Phase 5** | RFQ & Vendor Decision Quality | 3 synthetic vendors, deterministic scoring formula (0.50 cost + 0.30 latency + 0.20 reliability), quote-to-payment binding | **[COMPLETED]** | [`e441da0`](https://github.com/hacker9854-ship-it/AuRAG/commit/e441da0) |
| **Phase 6** | Industrial Economics & Explainability | Canonical 4.5h, $260k/hr, $1.17M exposure, 7,800,000:1 multiple, sensitivity sandbox, Explainability Drawer | **[COMPLETED]** | [`6e314b5`](https://github.com/hacker9854-ship-it/AuRAG/commit/6e314b5) |
| **Phase 7** | Evidence-Backed System Readiness Status | Eliminate hardcoded fake default fallbacks in UI; server-side sanitized DTO (`No credentials exposed`) | **[READY TO EXECUTE]** | `fix(machine-money): make readiness status evidence-backed` |
| **Phase 8** | README Final Polish & Truthful FAQ | 30-second explanation, What Is Live Today table, test snapshot link, superlative scrub, truthful FAQ | **[READY TO EXECUTE]** | `docs(readme): finalize submission readme and truthful disclosures` |
| **Phase 9** | Visual Evidence & Screenshot Refresh | Refresh and audit all 7 judge screenshots with current UI states | **[COMPLETED]** | [`c8a4ad3`](https://github.com/hacker9854-ship-it/AuRAG/commit/c8a4ad3) |
| **Phase 10** | Full E2E & Browser Playwright Verification | Complete automated Playwright browser test for all 3 scenarios, 85+ Pytest + 56+ Vitest verification | **[READY TO EXECUTE]** | `test(e2e): automate browser judge scenarios with playwright` |
| **Phase 11** | CI / Reproducibility & Security Guardrails | GitHub Actions CI workflow verification, secret scan pass, one-click local reproduction script | **[READY TO EXECUTE]** | `chore(ci): enforce final machine money verification gates` |
| **Phase 12** | Final Release Gate & Submission Checklist | 100% check against all Bitshala BOSS Battle criteria, compressed 90s judge demo rehearsal, submission freeze | **[READY TO EXECUTE]** | `chore(release): finalize hackathon submission package` |

---

## 3. Detailed Phase Specifications

```text
================================================================================
PHASE 0: BASELINE FREEZE & EVIDENCE MATRIX [STATUS: COMPLETED]
================================================================================
```
- **Goal:** Freeze authoritative baseline, audit all relative links, publish Claim-to-Evidence Matrix.
- **Deliverables:**
  - `docs/CURRENT_TEST_SNAPSHOT.md` (exact test counts, build results, timestamps).
  - `docs/CLAIM_EVIDENCE_MATRIX.md` (13 claims audited against code & tests).
  - 103 relative links audited with 0 broken links.
- **Commit:** [`c8a4ad3`](https://github.com/hacker9854-ship-it/AuRAG/commit/c8a4ad3)

```text
================================================================================
PHASE 1: PROTOCOL-SOUND BOLT11 INVOICES [STATUS: COMPLETED]
================================================================================
```
- **Goal:** Replace synthetic mock invoice strings with genuine, standards-valid BOLT11 invoices.
- **Deliverables:**
  - `backend/app/services/machine_money/bolt11.py`: Pure Python BIP-173 Bech32 and secp256k1 compact ECDSA encoder/decoder.
  - `MockLightningProvider`: Emits decodable BOLT11 regtest invoices with valid checksums and recoverable node pubkeys.
  - `tests/test_bolt11.py`: 5 dedicated unit tests verifying roundtrip decode, multipliers, and tamper rejection.
- **Commit:** [`25b6adf`](https://github.com/hacker9854-ship-it/AuRAG/commit/25b6adf)

```text
================================================================================
PHASE 2: GROUND JUDGE MODE IN ACTUAL RETRIEVAL [STATUS: READY TO EXECUTE]
================================================================================
```
- **Command:** `phase 2 start kro`
- **Goal:** Replace deterministic mock-only evidence generation in Stage 2 (`EVIDENCE_MATCHED`) with real hybrid GraphRAG retrieval, with an explicitly disclosed fallback when offline.
- **Target Files:**
  - `backend/app/services/machine_money/grounding.py` (New): Grounded evidence service accepting telemetry event, formulating search query, calling `retrieval.hybrid.retrieve` and `retrieval.graph_traversal.traverse`.
  - `backend/app/services/machine_money/service.py`: Wire `grounding.py` into `trigger_telemetry_flow()` Stage 2.
  - `frontend/components/machine-money/JudgeMode.tsx`: Display `HYBRID_RETRIEVAL` when live or `CONTROLLED DEMO FIXTURE` when fallback is used.
  - `tests/test_machine_money_grounding.py` (New): Unit and fallback tests for grounding service.
- **Acceptance Criteria:**
  - When Neo4j/Qdrant are active, Stage 2 executes actual hybrid retrieval for P-101A vibration query.
  - When offline, Stage 2 falls back gracefully and labels evidence as `CONTROLLED DEMO FIXTURE`.
  - Confidence gate: confidence < 0.75 triggers `PENDING_APPROVAL`, >= 0.75 proceeds to spending cap check.
  - Backend tests pass with 0 errors.
- **Commit Message:** `feat(machine-money): ground judge mode in hybrid graph retrieval`

```text
================================================================================
PHASE 3: STRENGTHEN CAUSAL PAYMENT EVIDENCE CHAIN [STATUS: READY TO EXECUTE]
================================================================================
```
- **Command:** `phase 3 start kro`
- **Goal:** Make the causal link from SCADA anomaly to settled satoshis visually undeniable in the UI and database.
- **Target Files:**
  - `frontend/components/machine-money/EvidenceAndProofDrawer.tsx`: Reorganize into 6 distinct tabs:
    1. `Why We Paid`: Telemetry reading, threshold breach, failure diagnosis, grounded evidence.
    2. `RFQ Decision`: 3 synthetic vendor bids, scoring weights, selection justification.
    3. `Policy Decision`: Spending cap check, confidence score, auto-pay authorization.
    4. `Lightning Proof`: BOLT11 invoice decode, payment hash, preimage verification, network mode badge.
    5. `Graph Lineage`: Neo4j entity relationships `(Payment)-[:FUNDS]->(WorkOrder)`.
    6. `Audit Ledger`: Relational database timestamps, idempotency key, immutable hash.
  - `backend/app/services/machine_money/service.py`: Ensure `get_payment_trail()` returns all 6 tabs' structured data.
  - `frontend/components/machine-money/EvidenceAndProofDrawer.test.tsx`: Verify all 6 tabs render correctly.
- **Acceptance Criteria:**
  - All 6 tabs navigate smoothly and display real/fixture evidence.
  - Top badge displays unambiguous mode: `MOCK / SIMULATION` or `LIVE LIGHTNING`.
  - Preimage check explicitly labeled: `Simulation integrity check` (mock) or `Lightning network settlement receipt` (live).
  - Frontend Vitest tests pass with 0 errors.
- **Commit Message:** `feat(machine-money): strengthen causal payment evidence chain`

```text
================================================================================
PHASE 4: FINALIZE DETERMINISTIC JUDGE SCENARIOS & RESET [STATUS: READY TO EXECUTE]
================================================================================
```
- **Command:** `phase 4 start kro`
- **Goal:** Perfect the 3 judge scenarios so they execute flawlessly in 60-90 seconds with complete state cleanup.
- **Target Files:**
  - `frontend/components/machine-money/JudgeMode.tsx`: Ensure 3 clean scenario triggers:
    - Primary CTA: `RUN INDUSTRIAL EMERGENCY` (Scenario A: 250 sats autonomous intervention).
    - Secondary: `POLICY ESCALATE` (Scenario B: 1,200 sats > 500 sat cap -> Operator Approval).
    - Secondary: `PROVIDER FAILURE` (Scenario C: 250 sats -> Channel liquidity failure -> 0 sats lost).
  - `frontend/app/machine-money/page.tsx`: Implement comprehensive `RESET DEMO` button that clears:
    - Execution timeline and active stage events.
    - Active payment selection and drawer state.
    - Simulation results and toast notifications.
  - `tests/test_machine_money_judge_mode.py`: Test scenario executions and reset state.
- **Acceptance Criteria:**
  - Fresh browser session can run all 3 scenarios sequentially without reloading or manual DB intervention.
  - Reset button resets UI to pristine state.
  - Timing labels say `Measured demo execution time` (not claiming real Lightning propagation when simulated).
- **Commit Message:** `feat(machine-money): finalize deterministic judge scenarios`

```text
================================================================================
PHASE 7: MAKE READINESS STATUS EVIDENCE-BACKED [STATUS: READY TO EXECUTE]
================================================================================
```
- **Command:** `phase 7 start kro`
- **Goal:** Eliminate misleading default placeholders in System Readiness and expose server-sanitized security diagnostics.
- **Target Files:**
  - `frontend/components/machine-money/SystemReadinessModal.tsx`:
    - Replace hardcoded defaults (`1.2 ms`, `1,000,000 sats`) with `"UNKNOWN / Not reported"` if backend doesn't provide them.
    - Security panel wording: Replace `0 Secrets in Memory` with `No credentials exposed by readiness endpoint`.
  - `backend/app/services/machine_money/service.py`: Add server-sanitized DTO endpoint for readiness diagnostics with 0 sensitive keys.
  - `frontend/components/machine-money/SystemReadinessModal.test.tsx`: Test truthful fallback display.
- **Acceptance Criteria:**
  - System readiness displays actual backend health or explicit "Not reported" fallback.
  - Security audit card reflects server-sanitized state.
  - Tests pass with 0 errors.
- **Commit Message:** `fix(machine-money): make readiness status evidence-backed`

```text
================================================================================
PHASE 8: README FINAL REWRITE & TRUTHFUL FAQ [STATUS: READY TO EXECUTE]
================================================================================
```
- **Command:** `phase 8 start kro`
- **Goal:** Polish `README.md` to deliver an immediate 30-second grasp of AuRAG, link to test snapshots, and provide truthful FAQs.
- **Target Files:**
  - `README.md`:
    - Top: 30-second value thesis + Machine Money feedback loop diagram.
    - "What Is Live Today" table contrasting Demo vs. Production Architecture.
    - Canonical parameter normalization (P-101A, 250 sats, 500 cap, 1200 escalation, 3 vendors, $1.17M).
    - Mandatory FAQ: "Is this live Bitcoin mainnet?", "Is the mock invoice a valid BOLT11 invoice?", "Is the industrial data real?".
    - Dynamic link to `docs/CURRENT_TEST_SNAPSHOT.md` instead of hardcoded test counts.
- **Acceptance Criteria:**
  - README passes automated claim and superlative audit.
  - All relative links verified with 0 broken links.
- **Commit Message:** `docs(readme): finalize submission readme and truthful disclosures`

```text
================================================================================
PHASE 10: FULL E2E & BROWSER PLAYWRIGHT VERIFICATION [STATUS: READY TO EXECUTE]
================================================================================
```
- **Command:** `phase 10 start kro`
- **Goal:** Automate browser-level judge validation using Playwright across all 3 scenarios.
- **Target Files:**
  - `frontend/tests/e2e/judge-mode.spec.ts` (New): Automated Playwright test:
    - Step 1: Navigate to `/machine-money`.
    - Step 2: Run Scenario A (Happy path) -> Verify settlement and 250 sats.
    - Step 3: Open Proof Drawer -> Verify 6 tabs and `MOCK / SIMULATION` badge.
    - Step 4: Run Scenario B (Policy Escalation) -> Verify `PENDING_APPROVAL` -> Click Approve -> Verify settlement.
    - Step 5: Reset Demo -> Run Scenario C (Failure) -> Verify 0 sat loss.
  - `frontend/playwright.config.ts`: Configured for headless CI and local execution.
- **Acceptance Criteria:**
  - Playwright test runs and passes with 0 timeouts or console errors.
  - Full suite passes: 85+ Pytest + 56+ Vitest + Playwright E2E.
- **Commit Message:** `test(e2e): automate browser judge scenarios with playwright`

```text
================================================================================
PHASE 11: CI / REPRODUCIBILITY & SECURITY GUARDRAILS [STATUS: READY TO EXECUTE]
================================================================================
```
- **Command:** `phase 11 start kro`
- **Goal:** Ensure any judge or CI runner can clone and reproduce results with a single command.
- **Target Files:**
  - `.github/workflows/ci.yml`: Workflow running backend pytest, frontend vitest, lint, build, and secret scan.
  - `scripts/verify_submission.ps1`: One-click PowerShell verification script running all tests and printing status summary.
  - `tests/test_secret_scan.py`: Ensures `.env` is uncommitted and zero credentials are exposed.
- **Acceptance Criteria:**
  - `verify_submission.ps1` runs cleanly from a fresh checkout.
  - GitHub Actions passes with green check.
- **Commit Message:** `chore(ci): enforce final machine money verification gates`

```text
================================================================================
PHASE 12: FINAL RELEASE GATE & SUBMISSION PACKAGE [STATUS: READY TO EXECUTE]
================================================================================
```
- **Command:** `phase 12 start kro`
- **Goal:** Perform final release audit, verify submission URLs, and freeze submission package.
- **Target Files:**
  - `docs/JUDGE_DEMO_SCRIPT.md`: Finalized 90-second rehearsal script with exact timestamps and voiceover cues.
  - `docs/FINAL_SUBMISSION_EVIDENCE.md`: Master submission evidence document referencing all commits, tests, screenshots, and architecture diagrams.
- **Acceptance Criteria:**
  - All 14 items on Final Release Gate marked `[PASS]`.
  - Repository pushed clean to `origin/main`.
- **Commit Message:** `chore(release): finalize hackathon submission package`

---

## 4. 60–90 Second Judge Demo Script

| Time | Stage | Action on Screen | Voiceover Cue |
| :---: | :--- | :--- | :--- |
| **0:00 - 0:15** | **The Problem** | Show P-101A telemetry card with vibration spiking to `5.4 mm/s` (threshold `4.5 mm/s`). | *"In heavy industry, a machine can detect its own failure hours in advance, but remains trapped waiting for human purchase orders. AuRAG gives machines governed financial agency."* |
| **0:15 - 0:35** | **Grounding & Evidence** | Click `RUN INDUSTRIAL EMERGENCY`. Timeline advances through Anomaly Detected -> Evidence Matched -> Failure Diagnosed. | *"AuRAG does not spend money from a raw sensor spike. It queries GraphRAG to ground the event in historical failure signatures (FE-001) and operating procedures (PROC-001)."* |
| **0:35 - 0:50** | **RFQ & Vendor Selection** | Timeline shows 3-vendor RFQ. Apex Diagnostics selected (250 sats, 15 min SLA). | *"A 3-node RFQ compares pre-approved industrial vendors using a balanced score of cost, latency, and reliability."* |
| **0:50 - 1:10** | **Policy Gate & Settlement** | Timeline shows Policy PASS (< 500 sats cap). Valid BOLT11 invoice generated with QR code, then transitions to SETTLED. | *"The spending policy enforces a strict 500-sat autonomous cap. Because 250 sats is within policy, the Lightning micro-payment settles autonomously."* |
| **1:10 - 1:30** | **Proof & Causal Lineage** | Click `Inspect Cryptographic Proof`. Open Proof Drawer. Navigate across Why We Paid, RFQ Decision, and Graph Lineage. | *"This is not just a payment—it is a verifiable causal chain. The payment hash is cryptographically bound to the work order, failure event, and Neo4j graph."* |
| **1:30 - 1:45** | **Human Escalation** | Click `POLICY ESCALATE`. Show 1,200 sats overhaul triggering `PENDING_APPROVAL`. Click `Approve`. | *"Above policy limits, autonomy stops immediately. The payment is held until a human operator signs off."* |
| **1:45 - 2:00** | **Business Impact** | Show Industrial Economics card: $1.17M modelled downtime exposure mitigated at a 7,800,000:1 multiple. | *"A 250-sat intervention protects against $1.17M in modelled downtime exposure. That is governed machine money in action."* |

---

## 5. Anti-Patterns / What NOT To Do

1. **Do NOT claim live Lightning mainnet** when running on mock or regtest.
2. **Do NOT commit private keys** or use hardcoded test keys outside test files.
3. **Do NOT skip tests** or lower assertions to force passes.
4. **Do NOT use fake superlative claims** ("first in the world", "unforgeable", "indisputable").
5. **Do NOT fabricate vendor APIs**—always label pre-approved vendors as synthetic demo nodes.
6. **Do NOT alter git history** or fake commit timestamps.

---

## 6. Definition of Done Checklist

- [x] **Phase 0:** Baseline Freeze & Evidence Matrix ([`0609a97`](https://github.com/hacker9854-ship-it/AuRAG/commit/0609a97), [`c8a4ad3`](https://github.com/hacker9854-ship-it/AuRAG/commit/c8a4ad3))
- [x] **Phase 1:** Protocol-Sound BOLT11 Invoices ([`25b6adf`](https://github.com/hacker9854-ship-it/AuRAG/commit/25b6adf))
- [ ] **Phase 2:** Ground Judge Mode in Actual Retrieval
- [ ] **Phase 3:** Strengthen Causal Payment Evidence Chain
- [ ] **Phase 4:** Finalize Deterministic Judge Scenarios & Reset
- [x] **Phase 5:** Bind RFQ Decision to Settlement Proof ([`e441da0`](https://github.com/hacker9854-ship-it/AuRAG/commit/e441da0))
- [x] **Phase 6:** Industrial Economics & Explainability ([`6e314b5`](https://github.com/hacker9854-ship-it/AuRAG/commit/6e314b5))
- [ ] **Phase 7:** Evidence-Backed System Readiness Status
- [ ] **Phase 8:** README Final Polish & Truthful FAQ
- [x] **Phase 9:** Visual Evidence & Screenshot Refresh ([`c8a4ad3`](https://github.com/hacker9854-ship-it/AuRAG/commit/c8a4ad3))
- [ ] **Phase 10:** Full E2E & Browser Playwright Verification
- [ ] **Phase 11:** CI / Reproducibility & Security Guardrails
- [ ] **Phase 12:** Final Release Gate & Submission Package