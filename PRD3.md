# PRD3: AuRAG — Machine Money Championship Build & Post-Audit Remediation

**Project:** AuRAG (Autonomous Retrieval-Augmented Graph)  
**Target:** Bitshala BOSS Battle 2026 — Machine Money Track  
**Execution Style:** Phase-gated, test-first, MCP-verified, commit-after-green  
**Master Execution PRD:** Refer to [AuRAG_FINAL_PRD.md](file:///c:/Users/nisha/OneDrive/Documents/Downloads/AuRAG/AuRAG_FINAL_PRD.md) for the authoritative live roadmap, phased gates, and completion checklist.  
**Master Goal:** Transform the AuRAG Machine Money implementation into a 100% judge-defensible, technically airtight, visually self-evident M2M payment system by eliminating all credibility gaps, reconciling documentation, standardizing metrics, and ensuring complete truthfulness between simulation and live Lightning settlement.

---

## 0. Master Execution Protocol for AI Agent

### 0.1 One-Command Phase Execution
The user will command one phase at a time using simple prompts such as:
- `phase 1 start kro`
- `phase 2 start kro`
- `phase X start kro`

When a phase command is received, the agent must:
1. **Identify Tasks**: Look up the target phase in Section 2 and isolate all assigned tasks.
2. **Inspect Current State**: Check actual codebase files before modifying.
3. **Implement**: Apply the exact code, schema, API, or UI changes required.
4. **End-to-End Test**:
   - Run backend `pytest` suite for any backend changes.
   - Run frontend `vitest` suite for any frontend changes.
   - Run Next.js production build (`npm run build`) to ensure zero TypeScript/lint regressions.
   - Use browser subagent or MCP tools to visually and functionally verify UI flows.
5. **Resolve Any Bugs**: If any test or build fails, iterate until 100% green. Do not skip or silence tests.
6. **Commit & Push**: Make a Git commit using the exact conventional commit message specified for that phase and push to `origin/main`.
7. **Report**: Provide a structured summary (files changed, tests run, commit hash, verification status) and wait for the user to command the next phase.

### 0.2 Definition of Done (DoD)
A phase is complete only when:
- All task acceptance criteria for that phase are satisfied.
- Automated tests (unit, integration, or E2E) pass with zero errors.
- UI behavior is verified via browser tools or DevTools MCP.
- Zero secrets or API keys are exposed.
- Mock vs. Live behavior is truthfully labeled across both UI and documentation.
- All changes are committed and pushed to GitHub.

### 0.3 Non-Negotiable Truthfulness & Provenance Rules
- **No Backdating**: Commit timestamps must reflect actual real-time execution. Never manipulate git history.
- **Explicit Simulation Disclosure**: All synthetic data, simulated preimages, regtest invoices, and mock providers must be clearly labeled `MOCK / SIMULATION`. Never masquerade simulated payments as real mainnet Bitcoin transactions.
- **Modelled Economic Estimates**: Downtime calculations ($1.17M exposure on PUMP-301) must be explicitly disclosed as **Modelled Estimates based on synthetic plant parameters**, not empirical historical losses.

---

## 1. Master Phase Roadmap & Execution Schedule

| Phase | Title | Focus & Audit Scope | Conventional Commit Message |
|:---:|:---|:---|:---|
| **Phase 1** | Settlement & Cryptographic Proof Honesty | BOLT11 invoice semantics, QR optical round-trip, backend-derived provider status, cryptographic proof wording split (Item 21.1, 21.2, 21.3) | `fix(machine-money): unify settlement honesty, bolt11 semantics, and proof verifiability` |
| **Phase 2** | Canonical Scenario Fixture & RFQ Binding | Centralize `JudgeScenarioFixture`, canonical 250 sats intervention amount, 3 synthetic vendors, bind RFQ selection downstream to payment proof (Item 21.4, 21.5, 21.15, 21.16) | `refactor(machine-money): centralize judge fixture, canonicalize amounts, and bind rfq to payment proof` |
| **Phase 3** | Economic Explainability & System Health Truthfulness | Visible ROI formulas, $1.17M modelled downtime exposure vs realized savings, truthful System Readiness diagnostics without fake nominal data (Item 21.8, 21.14, 21.17) | `feat(machine-money): expose economic derivation model and enforce truthful system readiness` |
| **Phase 4** | Claims, Superlatives & Architectural Honesty | Scrub unsupported superlatives ("first", "indisputable"), scope performance to measured test environments, separate "What Is Live Today" vs "Production Architecture" (Item 21.6, 21.7, 21.11) | `docs(readme): scrub superlatives, scope performance claims, and separate demo from production` |
| **Phase 5** | Canonical Test Suite & Verification Snapshot | Create `docs/CURRENT_TEST_SNAPSHOT.md`, execute full backend (77+ tests) & frontend (52+ tests) suites, verify production build (Item 21.12) | `test(machine-money): generate canonical test snapshot and verify end-to-end suite` |
| **Phase 6** | Visual Evidence Refresh & README Claim Matrix | Capture state-accurate screenshots (settled, policy escalation, failure), audit all README links and tree structure (0 broken links), publish Claim-to-Evidence Matrix (Item 21.9, 21.10, 21.13, 21.18) | `docs(readme): refresh evidence screenshots, audit links, and publish claim matrix` |
| **Phase 7** | Compressed Judge Walkthrough & Final Submission Gate | Update 90-second judge demo script, generate `docs/FINAL_SUBMISSION_EVIDENCE.md` audit report across all P0/P1 criteria (Item 21.19, 23, 25) | `docs(hackathon): finalize compressed judge walkthrough and submission evidence gate` |

---

## 2. Detailed Phase Specifications

```text
================================================================================
PHASE 1: SETTLEMENT & CRYPTOGRAPHIC PROOF HONESTY
================================================================================
```
### Focus
Address P0 credibility items regarding invoice validity, mock vs. live clarity, and cryptographic proof terminology.

### Tasks
- **Task 1.1 (Audit 21.1): BOLT11 Invoice & QR Optical Round-Trip Integrity**
  - Verify `Bolt11QRCode` renders using standard `qrcode.react`.
  - Validate invoice payloads: Ensure demo invoice strings follow standard `lnbc` / `lnbcrt` formatting with valid amount encoding or are explicitly marked `SIMULATED PAYMENT PAYLOAD`.
  - Add test proving QR renders and optical round-trip can decode the exact invoice string.
  - Add negative test verifying malformed invoices are flagged or handled safely.
- **Task 1.2 (Audit 21.2): Unified Backend-Derived Provider Status Contract**
  - Establish a single canonical provider status schema returned by the backend:
    ```json
    {
      "provider_mode": "MOCK",
      "network": "REGTEST",
      "settlement_source": "SIMULATED",
      "is_live": false
    }
    ```
  - Bind all frontend UI components (`ProviderModeBadge`, `JudgeMode`, `PaymentProofDrawer`, `ExecutionTimeline`) to this backend status rather than relying on frontend-only environment flags.
  - Display clear badges: `MOCK / SIMULATION` on regtest or `LIVE LIGHTNING`.
- **Task 1.3 (Audit 21.3): Cryptographic Proof Wording Split**
  - Refine proof verification semantics:
    - In Mock Mode: Label as **"Simulation Integrity Verified: SHA-256(preimage) matches payment_hash"**.
    - In Live Mode: Label as **"Network Settlement Verified: Lightning Node settled receipt confirmed"**.
  - Update `ProofVerification.tsx` and `PaymentProofDrawer.tsx` to display this distinction clearly.

### Acceptance Criteria
- [ ] QR encodes the exact payload string and optical test verifies decoding.
- [ ] Provider status is 100% backend-derived and visible before executing payment.
- [ ] Settlement receipt and proof drawer explicitly distinguish simulation integrity from live network settlement.
- [ ] Frontend Vitest and backend Pytest pass with 0 failures.

### Target Commit
```bash
git commit -m "fix(machine-money): unify settlement honesty, bolt11 semantics, and proof verifiability"
```

---

```text
================================================================================
PHASE 2: CANONICAL SCENARIO FIXTURE & RFQ-TO-PAYMENT BINDING
================================================================================
```
### Focus
Eliminate conflicting numbers, centralize the industrial demo scenario, and connect the RFQ vendor selection directly into the payment and proof chain.

### Tasks
- **Task 2.1 (Audit 21.15): Centralize Canonical `JudgeScenarioFixture`**
  - Create a single source of truth for the demo scenario (`JudgeScenarioFixture` in backend and frontend shared config):
    - `site_id`: `"SITE-TX-401"`
    - `equipment_id`: `"PUMP-301"` (or `"P-101A"` canonicalized throughout)
    - `sensor_id`: `"VIB-301-BEARING"`
    - `reading`: `5.4` mm/s (threshold: `4.5` mm/s, ISO 10816 Zone C)
    - `failure_signature`: `"FE-001"` (Bearing inner race spalling)
    - `procedure_id`: `"PROC-001"` (Vibration Diagnostics & Bearing Lubrication)
    - `service_type`: `"vibration_analysis_dispatch"`
    - `canonical_payment_sats`: `250` sats (reconciling stray 50 or 25,000 sats values)
    - `spending_cap_sats`: `500` sats
- **Task 2.2 (Audit 21.4): Reconcile Economics Amounts & Derived Metrics**
  - Ensure all UI components, tests, and documentation reflect `250 sats` as the canonical intervention amount for the happy path.
  - Derived ROI and multiple ratios must calculate deterministically from `250 sats` (~$0.15 at $60,000/BTC).
- **Task 2.3 (Audit 21.5 & 21.16): Multi-Vendor RFQ Reconciliation & Downstream Binding**
  - Standardize on exactly 3 synthetic pre-approved vendors:
    1. *Apex Diagnostics* (250 sats, 1.2h SLA, 99.4% rating, pubkey `02a1...`)
    2. *Precision Dynamics* (320 sats, 0.8h SLA, 98.9% rating, pubkey `03b2...`)
    3. *Quantum Reliability* (450 sats, 2.5h SLA, 97.5% rating, pubkey `02c3...`)
  - Label vendors explicitly as `Pre-approved Synthetic Vendor Node`.
  - Propagate the winning RFQ vendor ID, name, and pubkey directly into the generated invoice, payment receipt, and `PaymentProofDrawer`.
  - Expose the explainable scoring formula: `Score = (0.5 * CostNorm) + (0.3 * LatencyNorm) + (0.2 * SLANorm)`.

### Acceptance Criteria
- [ ] Canonical scenario fixture used across backend, frontend, tests, and demo presets.
- [ ] No conflicting intervention amounts (50 sats vs 250 sats vs 25,000 sats) remain.
- [ ] Exactly 3 vendors displayed and clearly marked as pre-approved synthetic nodes.
- [ ] Winning RFQ vendor is bound downstream to the settled payment proof.
- [ ] All tests pass.

### Target Commit
```bash
git commit -m "refactor(machine-money): centralize judge fixture, canonicalize amounts, and bind rfq to payment proof"
```

---

```text
================================================================================
PHASE 3: ECONOMIC EXPLAINABILITY & SYSTEM HEALTH TRUTHFULNESS
================================================================================
```
### Focus
Prevent misrepresentation of modelled financial estimates as empirical savings and ensure system diagnostics never display fictitious nominal health.

### Tasks
- **Task 3.1 (Audit 21.8 & 21.17): Economic Exposure vs Realized Savings & Formula Explainability**
  - Update all financial copy across `IndustrialEconomicsCard.tsx`, README, and docs:
    - Change "Loss Prevented" to **"Modelled Downtime Exposure: $1.17M"** (based on synthetic 4.5h outage at $260k/hr).
    - Display explicit disclaimer: `Modelled estimate based on synthetic industrial facility parameters`.
  - Add an inspectable formula drawer/popover in `IndustrialEconomicsCard.tsx`:
    - `Modelled Downtime Exposure = Avoided Outage Duration (4.5h) × Outage Cost Rate ($260,000/h) = $1,170,000`.
    - `Intervention Cost = 250 sats ≈ $0.15 (at $60k/BTC)`.
    - `Protection Multiple = $1,170,000 / $0.15 ≈ 7,800,000 : 1`.
  - Include interactive sensitivity sliders for outage hours and hourly rate.
- **Task 3.2 (Audit 21.14): System Readiness Truthfulness**
  - Update `SystemReadinessModal.tsx` and health indicators:
    - Never invent fake nominal values (`1.2ms`, dummy wallet balances, or mock connections labeled "Nominal").
    - Use strict truthful states: `CONNECTED`, `DEGRADED`, `DISCONNECTED`, `UNKNOWN`, or `DEMO VALUE (MOCK)`.
    - Show "ALL SYSTEMS NOMINAL" only when actual live network checks pass; otherwise display "SIMULATION ENVIRONMENT READY".

### Acceptance Criteria
- [ ] Economics views show `MODELLED / SYNTHETIC` badge and formulas are fully inspectable.
- [ ] No claim asserts AuRAG has empirically prevented $1.17M in a real plant.
- [ ] System Readiness shows truthful diagnostic states and never presents dummy data as live health.
- [ ] Tests verify formula calculations and readiness states.

### Target Commit
```bash
git commit -m "feat(machine-money): expose economic derivation model and enforce truthful system readiness"
```

---

```text
================================================================================
PHASE 4: CLAIMS, SUPERLATIVES & ARCHITECTURAL HONESTY
================================================================================
```
### Focus
Scrub unsupported superlatives, scope performance numbers to measured environments, and clearly demarcate current demo capabilities from production architecture.

### Tasks
- **Task 4.1 (Audit 21.6): Scrub Unsupported Superlatives & Absolute Claims**
  - Search and replace unprovable marketing claims across all docs and UI:
    - Replace *"first industrial-grade implementation"* with *"an industrial-grade implementation"*.
    - Replace *"indisputable"* or *"guaranteed zero downtime"* with *"verifiable cryptographic audit trail"* and *"designed for zero unplanned downtime"*.
- **Task 4.2 (Audit 21.7): Scope Performance Claims to Measured Environments**
  - Disclose the execution environment alongside any timing metrics:
    - Demo execution latency: `~412ms` (Measured on local simulated runtime / Railway container).
    - Note that real Bitcoin Lightning finality depends on channel routing latency (typically 500ms–2000ms).
- **Task 4.3 (Audit 21.11): Explicit "What Is Live Today" vs "Production Target Architecture"**
  - Add clear side-by-side architecture section in `README.md` and `docs/`:
    - **What Is Live Today**:
      - Next.js 16 frontend on Vercel (`au-rag.vercel.app`).
      - FastAPI backend on Railway (`aurag-production.up.railway.app`).
      - Lightning settlement on `MockLightningProvider` (`regtest` simulation).
      - Multi-vendor RFQ engine with 3 pre-approved deterministic vendor bids.
      - GraphRAG reasoning over Neo4j ontology.
    - **Production Target Architecture**:
      - Pluggable `LightningProviderInterface` connecting directly to LNbits / Core Lightning / LND mainnet nodes via REST or gRPC.
      - External vendor webhook protocol with secp256k1 signature validation.

### Acceptance Criteria
- [ ] Codebase, README, and demo script are free of unprovable superlatives.
- [ ] Timing and latency metrics include measured environment disclaimers.
- [ ] README contains the explicit "What Is Live Today" vs "Production Architecture" matrix.

### Target Commit
```bash
git commit -m "docs(readme): scrub superlatives, scope performance claims, and separate demo from production"
```

---

```text
================================================================================
PHASE 5: CANONICAL TEST SUITE & VERIFICATION SNAPSHOT
================================================================================
```
### Focus
Run complete end-to-end verification, resolve any regressions, and generate an authoritative test count snapshot.

### Tasks
- **Task 5.1 (Audit 21.12): Authoritative Test Execution**
  - Execute backend pytest suite:
    ```bash
    pytest -v tests/ --tb=short
    ```
  - Execute frontend vitest suite:
    ```bash
    npm --prefix frontend test -- --run
    ```
  - Verify Next.js production build:
    ```bash
    npm --prefix frontend run build
    ```
  - Run secret scanning script to guarantee zero leaked credentials.
- **Task 5.2: Generate `docs/CURRENT_TEST_SNAPSHOT.md`**
  - Document the exact counts from the authoritative run:
    - Backend Pytest tests passed.
    - Frontend Vitest suites and tests passed.
    - Next.js build compilation status (routes, compile time).
    - Timestamp and commit SHA.
  - Reconcile README badges and text to match this single canonical count.

### Acceptance Criteria
- [ ] 100% of backend and frontend tests pass.
- [ ] Next.js production build completes with 0 errors.
- [ ] `docs/CURRENT_TEST_SNAPSHOT.md` generated and synced with README badge.

### Target Commit
```bash
git commit -m "test(machine-money): generate canonical test snapshot and verify end-to-end suite"
```

---

```text
================================================================================
PHASE 6: VISUAL EVIDENCE REFRESH & README CLAIM MATRIX
================================================================================
```
### Focus
Update visual evidence to match current states, audit repository links, and build the definitive Claim-to-Evidence Matrix.

### Tasks
- **Task 6.1 (Audit 21.9): Screenshot Evidence Refresh**
  - Capture state-accurate screenshots from the live deployment or local environment using DevTools MCP:
    1. Judge Mode Console (Above-the-fold)
    2. Execution Timeline (In-flight & Settled)
    3. Settled Receipt & Payment Proof Drawer (with cryptographic hash match)
    4. Policy Escalation Modal (>500 sats human approval required)
    5. Provider Failure / Fallback Handling
    6. Industrial Economics & Assumptions Drawer
  - Place screenshots in `docs/screenshots/` with descriptive captions.
- **Task 6.2 (Audit 21.10 & 21.13): README Restructuring & Link Audit**
  - Restructure README for judge-first discovery: Problem → 30-sec summary → Live links → Screenshots → M2M flow → Architecture → Tests.
  - Test every relative and absolute link in `README.md` to ensure 0 broken links.
- **Task 6.3 (Audit 21.18): Final README Claim-to-Evidence Matrix**
  - Include the comprehensive verification table in `README.md`:
    | Claim | Implementation & Proof | Status |
    |---|---|---|
    | Standards-Compliant QR | `qrcode.react` with optical decode test | PASS ✅ |
    | Truthful Settlement | Backend `provider_mode: MOCK`, explicitly labeled | PASS ✅ |
    | Cryptographic Preimage Proof | `SHA256(preimage) === payment_hash` verified | PASS ✅ |
    | Multi-Vendor RFQ | 3 pre-approved vendors with transparent scoring | PASS ✅ |
    | Policy Spending Cap | >500 sats rejected with HTTP 403 / Human Escalation | PASS ✅ |
    | Deterministic Idempotency | SHA-256 idempotency cache prevents double-spend | PASS ✅ |
    | Modelled Economics | $1.17M exposure with inspectable assumptions | PASS ✅ |
    | Zero Secrets Leaked | 350+ files scanned, zero exposed credentials | PASS ✅ |

### Acceptance Criteria
- [ ] All screenshots in README correspond to exact visual states.
- [ ] Zero broken links in `README.md` or `docs/`.
- [ ] Claim-to-Evidence Matrix prominently featured.

### Target Commit
```bash
git commit -m "docs(readme): refresh evidence screenshots, audit links, and publish claim matrix"
```

---

```text
================================================================================
PHASE 7: COMPRESSED JUDGE WALKTHROUGH & FINAL SUBMISSION GATE
================================================================================
```
### Focus
Deliver a punchy 90-second judge demo script and the final submission sign-off report.

### Tasks
- **Task 7.1 (Audit 21.19): Compressed 90-Second Judge Demo Script**
  - Update `docs/JUDGE_DEMO_SCRIPT.md` to feature a high-impact, tight walkthrough:
    - `0:00 - 0:15`: The Industrial Problem ($260k/hr downtime, slow procurement).
    - `0:15 - 0:30`: Trigger Emergency (Click "Happy Path Intervene").
    - `0:30 - 0:50`: GraphRAG Diagnosis & 3-Vendor RFQ Selection.
    - `0:50 - 1:10`: Policy Gate & Lightning Settlement (sub-second simulated finality).
    - `1:10 - 1:30`: Inspect Payment Proof Drawer (SHA-256 cryptographic check).
    - `1:30 - 1:45`: Industrial Economics ($1.17M modelled downtime exposure).
    - `Optional`: 15-second demonstration of Policy Escalation (>500 sats).
- **Task 7.2 (Audit 23 & 25): Final Submission Gate Report**
  - Generate `docs/FINAL_SUBMISSION_EVIDENCE.md` certifying:
    - Repository commit hash and branch status.
    - Exact test counts and execution times.
    - Truthfulness confirmation (simulation disclosures active, no fake mainnet claims).
    - Policy cap verification (>500 sats gate active).
    - Provenance audit (zero backdated timestamps).
    - Live deployment URLs and health status.

### Acceptance Criteria
- [ ] `docs/JUDGE_DEMO_SCRIPT.md` contains the compressed 90-second walkthrough with timestamps and talking points.
- [ ] `docs/FINAL_SUBMISSION_EVIDENCE.md` is complete and signed off.
- [ ] Git repository is 100% clean and pushed to `origin/main`.

### Target Commit
```bash
git commit -m "docs(hackathon): finalize compressed judge walkthrough and submission evidence gate"
```

---

## 3. End-to-End Command Sequence for User

The user drives execution using the following exact commands:

```text
1. phase 1 start kro  --> Settlement & Cryptographic Proof Honesty
2. phase 2 start kro  --> Canonical Scenario Fixture & RFQ Binding
3. phase 3 start kro  --> Economic Explainability & System Health Truthfulness
4. phase 4 start kro  --> Claims, Superlatives & Architectural Honesty
5. phase 5 start kro  --> Canonical Test Suite & Verification Snapshot
6. phase 6 start kro  --> Visual Evidence Refresh & README Claim Matrix
7. phase 7 start kro  --> Compressed Judge Walkthrough & Final Submission Gate
```

After each phase is completed, tested, verified, and committed, the agent reports completion and awaits the next command.
