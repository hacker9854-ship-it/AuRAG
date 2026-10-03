# PRD: AuRAG — Machine Money Championship Build

**Project:** AuRAG
**Target:** BOSS Battle 2026, Machine Money track
**Execution style:** Phase-gated, test-first, commit-after-green
**Primary goal:** Turn the existing AuRAG Machine Money implementation into a judge-ready, technically defensible, visually obvious end-to-end M2M payment system without misrepresenting mock behavior, evidence, or development history.

---

## 0. IMPORTANT EXECUTION RULES

This file is the master implementation contract for an agent working on the repository. The user will invoke one phase or task at a time. The agent must execute only the requested phase/task, complete the acceptance criteria, run the required tests, and create the requested commit before reporting completion.

### 0.1 One-command / one-gated-task execution

When the user says something such as:

- `Execute Phase 0`
- `Execute Task 2.3`
- `Run the next task`

the agent must:

1. Read this PRD and identify the exact task.
2. Inspect the current repository state before editing.
3. Make the smallest coherent implementation needed for that task.
4. Add or update tests before claiming the task is done.
5. Run the task-specific tests.
6. Run the relevant regression suite.
7. Fix failures caused by the change.
8. Update documentation/checklists when the task changes behavior.
9. Create a Git commit using the exact commit format defined in Section 4.
10. Report: files changed, behavior added/fixed, tests run, result, commit hash, and any remaining risk.

Do not silently skip tests. Do not silently move to a later phase. Do not make unrelated refactors while a task is in progress.

### 0.2 Definition of Done

A task is complete only when:

- Acceptance criteria are met.
- Automated tests exist for new critical behavior.
- Existing relevant tests still pass.
- UI behavior is manually inspected when the task is visual.
- No secrets are introduced.
- Mock vs. live behavior is truthfully labeled.
- Documentation reflects the actual implementation.
- The task is committed.

### 0.3 Non-negotiable truthfulness rule

Never fabricate evidence, fake a live payment, mislabel a mock provider as real Lightning, or manipulate repository history to make an old implementation appear to have been created during a hackathon window.

Do **not**:

- backdate commits;
- alter author/committer timestamps to fabricate an earlier development timeline;
- create fake historical commits;
- rewrite history solely to deceive judges about when code was built;
- manufacture transaction hashes, invoices, or payment receipts and present them as live network events;
- copy a prior hackathon project wholesale when the target event rules prohibit pre-existing code.

The correct remediation is an honest audit, transparent documentation, new work recorded with real timestamps, and, where eligibility requires it, a clean rebuild or organizer-approved reuse path.

---

# 1. CURRENT REPOSITORY AUDIT

The supplied AuRAG repository already contains substantial Machine Money infrastructure:

- `backend/app/services/machine_money/schemas.py`
- `backend/app/services/machine_money/service.py`
- `backend/app/services/machine_money/bridge.py`
- `backend/app/services/machine_money/registry.py`
- `backend/app/services/machine_money/providers/base.py`
- `backend/app/services/machine_money/providers/mock.py`
- `backend/app/services/machine_money/providers/lnbits.py`
- `backend/app/services/machine_money/providers/factory.py`
- `backend/app/services/machine_money/graph.py`
- `frontend/app/machine-money/page.tsx`
- `tests/test_machine_money_task3.py`
- `tests/test_machine_money_task4.py`
- `tests/test_machine_money_task5.py`
- `tests/test_machine_money_task6.py`
- `tests/test_e2e_machine_money.py`

The project also has a mature GraphRAG, telemetry, agent, retrieval, evaluation, and ingestion stack.

### 1.1 Confirmed technical issue: QR implementation

The current `Bolt11QRCode` in `frontend/app/machine-money/page.tsx` renders a deterministic pseudo-grid derived from the invoice string. It visually resembles a QR code but is not a standards-compliant QR encoder.

This must be replaced with a real QR encoder.

### 1.2 Confirmed product issue: demo complexity

The current Machine Money page contains a multi-stage lifecycle and multiple controls, but the judge must understand the core story immediately. A dedicated `Judge Mode` / `Run Industrial Emergency` experience is required.

### 1.3 Confirmed product issue: analytics depth

A generic activity/earnings analytics pattern is not sufficiently differentiated for AuRAG. The LightningTime project demonstrated a useful product pattern: a simple live action loop, clear payment state, transaction visibility, and lightweight analytics. AuRAG should adapt those patterns into **Machine Money Intelligence / Industrial Economics**, not copy generic productivity analytics.

### 1.4 Confirmed architecture requirement: mock/live clarity

The repository already has `MockLightningProvider` and `LNbitsProvider`. The UI and docs must make the provider mode unambiguous:

- `MOCK / SIMULATION` for deterministic offline demos and CI.
- `LIVE LIGHTNING` for actual configured Lightning infrastructure.

A simulated invoice or settlement must never be described as an actual network payment.

### 1.5 Git-integrity status

The working repository contains an active `.git` directory on branch `main` with tracked commit history and remote configuration. Historical commits and working tree status can be inspected directly without guesswork.

The PRD includes a **Git Integrity Gate** (Phase 0) that records actual history without backdating, rewriting, or falsifying timestamps.

---

# 2. PRODUCT VISION

## 2.1 Core narrative

AuRAG is not a generic crypto wallet and not merely a RAG chatbot.

The system demonstrates:

> **Machine detects operational risk → AuRAG reasons over evidence → service is selected → spending policy is evaluated → Lightning payment is authorized or escalated → settlement is recorded → payment is linked back into the operational graph → the business outcome is visible.**

## 2.2 North-star demo

A judge should be able to click one control and watch a complete, understandable story in seconds:

```text
Telemetry anomaly
      ↓
GraphRAG evidence
      ↓
Root-cause / service recommendation
      ↓
Vendor quote
      ↓
Policy gate
   ↙        ↘
auto-pay     human approval
   ↓             ↓
Lightning settlement
      ↓
Proof + audit
      ↓
Work-order outcome
      ↓
Industrial economic impact
```

## 2.3 Product promise

Every autonomous payment should answer five questions:

1. **Why did we pay?**
2. **What evidence justified the action?**
3. **Why was this amount allowed?**
4. **Where did the payment go?**
5. **What operational outcome did it fund?**

---

# 3. LIGHTNINGTIME PATTERNS TO ADAPT, NOT CLONE

The second project, LightningTime, is a useful source of product patterns. Use the ideas below only in a way permitted by the target hackathon's rules and only where they improve AuRAG's own Machine Money story.

## 3.1 Adopt

### A. Simple real-time payment loop

Adapt the feeling of:

`action → payment → visible result`

to:

`detect → reason → quote → authorize → pay → outcome`

### B. Clear wallet/payment state

Prominently show:

- wallet/provider status;
- network/mode;
- total/available demo balance when applicable;
- pending transactions;
- settled transactions.

### C. Transaction history

Make the payment ledger useful and inspectable. Each row should expose enough metadata to open a detailed evidence/proof drawer.

### D. Lightweight analytics

Transform generic activity analytics into **Industrial Economics**:

- machine-money spend;
- autonomous payments;
- human approvals;
- pending/rejected transactions;
- average settlement time;
- estimated downtime exposure;
- estimated intervention cost;
- service/vendor SLA metrics;
- cost-vs-risk comparison where assumptions are explicit.

### E. Demo simplicity

Use a strong primary action rather than making the judge discover the feature set manually.

## 3.2 Do not adopt blindly

Do not add generic attendance/time-tracking concepts, SBTs, or unrelated productivity features.

Do not copy another project's credentials, private configuration, or implementation details.

Do not replicate another project's product identity.

---

# 4. GIT INTEGRITY + COMMIT STRATEGY

## 4.1 Objective

Create a clean, auditable development trail from the current moment onward and resolve any eligibility concern honestly.

## 4.2 Commit format

Use conventional, descriptive commits:

```text
feat(machine-money): add judge mode
fix(machine-money): replace pseudo qr with standards-compliant encoder
test(machine-money): add live-mode and qr regression coverage
refactor(machine-money): isolate payment proof presentation
docs(hackathon): document demo mode and eligibility assumptions
chore(hackathon): add verification scripts
```

## 4.3 Required integrity audit

The first Git task must collect, without modifying history:

```bash
git status

git log --date=iso --pretty=format:'%h | %ad | %an | %s' --all -n 100

git log --graph --decorate --oneline --all -n 100

git branch -a

git remote -v

git show --stat --oneline HEAD
```

Then determine:

- earliest relevant AuRAG commit;
- whether the repository was public before the target event;
- whether major Machine Money code predates the allowed build window;
- whether the event rules permit pre-existing code or require work during a specified window;
- whether a fresh rebuild or organizer confirmation is necessary.

## 4.4 Allowed remediation

If history reveals a real eligibility problem:

1. Preserve the original history.
2. Record the finding in `docs/HACKATHON_ELIGIBILITY.md`.
3. If permitted, create a new branch containing the compliant development path.
4. If prior code cannot legally be reused, rebuild the affected functionality in the allowed window rather than altering timestamps.
5. Seek organizer clarification when the rules are ambiguous.

## 4.5 Forbidden remediation

Never execute commands such as:

```bash
git commit --date="past-date"
git filter-branch ...
git rebase ... --exec "rewrite timestamps"
```

for the purpose of manufacturing an earlier build timeline.

Do not use any equivalent mechanism through an IDE, CI job, GitHub API, or agent.

---

# 5. TARGET UX

## 5.1 Primary route

`/machine-money`

## 5.2 Primary UI hierarchy

The page must be organized in this visual order:

1. **System mode + provider status**
2. **Judge Mode / Run Industrial Emergency**
3. **Live execution timeline**
4. **Core decision evidence**
5. **Payment proof**
6. **Operational graph trail**
7. **Vendor / economics comparison**
8. **Transaction ledger**
9. **Detailed technical evidence**

## 5.3 Judge Mode

Primary CTA:

`▶ RUN INDUSTRIAL EMERGENCY`

When clicked, it launches a deterministic scenario and animates these stages:

```text
00.0s  Sensor anomaly detected
00.3s  GraphRAG evidence matched
00.7s  Service/vendor quote resolved
01.0s  Spending policy evaluated
01.2s  BOLT11 invoice generated
01.5s  Payment authorized
01.8s  Settlement confirmed
02.0s  Audit + graph linkage committed
02.2s  Work-order outcome displayed
```

Actual timings may differ. The UI must display measured timings, not hardcoded fake durations.

## 5.4 Execution timeline contract

Each stage needs:

- timestamp / elapsed time;
- status;
- machine-readable event type;
- short human-readable explanation;
- evidence reference where available.

The backend should emit structured events rather than the frontend inventing them.

---

# 6. FUNCTIONAL REQUIREMENTS

## FR-01: Standards-compliant BOLT11 QR

Replace the pseudo-grid implementation with a real QR encoder.

Requirements:

- standards-compliant QR generation;
- reliable scanner compatibility;
- error correction level appropriate for a visual payment request;
- copy invoice action retained;
- accessible text fallback retained;
- clear label showing `MOCK / SIMULATION` or `LIVE LIGHTNING`;
- tests verify the rendered QR encodes the exact invoice string.

## FR-02: Judge Mode

Implement one-click deterministic end-to-end demonstration.

Requirements:

- resettable scenario;
- visible execution timeline;
- no page reload required;
- handles success and policy-escalation cases;
- does not bypass real backend policy;
- displays provider mode explicitly;
- produces an inspectable final evidence package.

## FR-03: Machine Money Intelligence

Create a dedicated analytics layer.

Minimum metrics:

- total machine-money spend;
- settled spend;
- pending amount;
- number of autonomous payments;
- number of human approvals;
- rejection count;
- average settlement latency;
- quote-to-payment conversion;
- service/vendor distribution;
- estimated downtime exposure;
- estimated intervention cost.

All business-impact metrics must include:

- label `Estimated` when model-based;
- source or assumption metadata;
- no fabricated certainty.

## FR-04: Multi-vendor RFQ

For a maintenance action, support multiple service candidates.

Example presentation:

```text
Vendor A   250 sats   2.0h SLA   98% reliability
Vendor B   180 sats   3.0h SLA   91% reliability
Vendor C   320 sats   1.0h SLA   99% reliability
```

Selection must be rule/model driven and explainable.

Required explanation format:

```text
Selected vendor: Vendor C
Reason: Fastest SLA within the authorized spending policy.
```

The exact scoring model must be documented. Never imply real-world reliability unless the data source actually supports it. Synthetic values must be labeled as synthetic.

## FR-05: Policy gate

Policy evaluation must remain a hard backend boundary.

Default demo policy:

```text
AUTONOMOUS CAP = 500 sats
```

For amounts within the configured cap and when auto-pay is enabled:

```text
AUTHORIZED → EXECUTE
```

For amounts above the cap or when auto-pay is disabled:

```text
PENDING_APPROVAL → HUMAN REVIEW
```

The frontend may display the result but must not implement the authoritative spending rule.

## FR-06: Human-in-the-loop approval

Approval flow must expose:

- payment ID;
- amount;
- vendor;
- work order;
- triggering event;
- evidence summary;
- policy reason;
- approver identity;
- approval timestamp;
- final settlement state.

## FR-07: Payment Proof Drawer

Clicking a settled transaction opens a proof drawer with:

- payment ID;
- amount;
- provider;
- mode/network;
- BOLT11 invoice;
- payment hash;
- preimage when provided by provider;
- fee;
- settlement timestamp;
- idempotency key;
- work-order ID;
- predictive-event ID;
- policy ID;
- policy decision;
- graph linkage status;
- audit ledger status.

Never expose private keys, admin keys, invoice keys, or other secrets.

## FR-08: Graph Trail

Visualize:

```text
Equipment
   ↓
Predictive Event
   ↓
Failure Signature / Evidence
   ↓
Work Order
   ↓
Payment
   ↓
Service Provider
```

The payment node should visibly connect the financial action to the operational reason.

## FR-09: Proof verification

Add a deterministic proof verification action.

Minimum verification:

```text
SHA-256(preimage) == payment_hash
```

Only perform this check when the underlying data is actually available.

For mock mode, label the result:

`SIMULATED CRYPTOGRAPHIC VERIFICATION`

For live mode, label it according to the actual provider/network evidence.

## FR-10: Demo mode separation

All provider states must be explicit.

Required UI labels:

```text
MOCK / SIMULATION
```

or

```text
LIVE LIGHTNING
```

The status must be derived from backend provider metadata.

## FR-11: Transaction lifecycle

Use a consistent state machine:

```text
QUOTED
→ INVOICE_CREATED
→ PENDING / PENDING_APPROVAL
→ AUTHORIZED
→ PAID / SETTLED
```

Failure and exceptional states must remain supported:

```text
FAILED
REJECTED
EXPIRED
REFUNDED
```

## FR-12: Idempotency

Same logical event + service + asset combination must not cause duplicate payments.

Duplicate requests should return or reference the existing payment according to the existing service contract.

## FR-13: Failure simulation

Judge Mode must have at least these controlled paths:

### Scenario A: autonomous

```text
250 sats ≤ 500-sat cap
→ autonomous settlement
```

### Scenario B: policy escalation

```text
1,200 sats > 500-sat cap
→ pending approval
```

### Scenario C: provider failure

Simulate provider failure and show:

```text
Payment not executed
Audit recorded
Retry guidance shown
No duplicate charge
```

### Scenario D: duplicate trigger

Re-send the same logical trigger and prove that the idempotency guard prevents duplicate settlement.

## FR-14: Industrial Economics

Add an economic context panel.

Example:

```text
ESTIMATED DOWNTIME EXPOSURE
4.5 hours

ESTIMATED EXPOSURE VALUE
$1.17M

INTERVENTION COST
250 sats

DATA BASIS
Synthetic plant model
```

This is a **modelled estimate**, not a claimed real plant loss. The calculation and assumptions must be inspectable.

## FR-15: Responsive judge experience

Machine Money must work cleanly on:

- desktop 1440px+
- laptop 1280px+
- tablet width;
- narrow mobile width.

No critical proof or CTA may become inaccessible on smaller screens.

---

# 7. BACKEND REQUIREMENTS

## BE-01: Structured execution events

Create/standardize an event contract for Judge Mode.

Suggested shape:

```json
{
  "execution_id": "EXEC-...",
  "stage": "POLICY_CHECK",
  "status": "SUCCESS",
  "elapsed_ms": 142,
  "message": "250 sats is within autonomous cap",
  "evidence_refs": ["POL-LIGHTNING-MACHINE-MONEY"]
}
```

Do not expose secret provider credentials in event payloads.

## BE-02: Machine Money execution orchestrator

The orchestration path must remain:

```text
telemetry
→ evidence
→ service quote/RFQ
→ policy
→ invoice
→ payment
→ audit
→ graph persistence
```

No frontend-only shortcut may bypass a backend boundary.

## BE-03: Multi-vendor quote API

Add a service that returns multiple candidates for the same maintenance intent.

Requirements:

- deterministic demo data;
- synthetic-data labeling;
- quote validity timestamps;
- explainable selection;
- test coverage.

## BE-04: Proof package API

Add one backend response that can provide all non-secret proof data for a payment.

Suggested response groups:

```text
identity
payment
policy
operational_context
cryptographic_proof
graph_links
audit
provider_mode
```

## BE-05: Industrial economics API

Return:

- intervention cost;
- downtime estimate;
- exposure estimate;
- assumptions;
- data source label;
- computation version.

## BE-06: QR payload API compatibility

The backend remains the source of truth for the BOLT11 invoice string. The frontend QR renderer must encode that exact string.

## BE-07: Provider health

Provider health should distinguish:

- connected;
- simulation;
- network;
- latency;
- balance when available;
- provider name.

---

# 8. FRONTEND REQUIREMENTS

## FE-01: Remove pseudo QR

Delete the custom pseudo-random matrix implementation.

Do not retain fake QR fallback unless it is clearly an unavailable-state placeholder, and it must never be shown as a usable payment QR.

## FE-02: Judge Mode component

Create a dedicated component structure, for example:

```text
components/machine-money/
  JudgeMode.tsx
  ExecutionTimeline.tsx
  PaymentProofDrawer.tsx
  VendorRFQ.tsx
  IndustrialEconomics.tsx
  ProviderModeBadge.tsx
  ProofVerification.tsx
  TransactionLedger.tsx
```

Exact file names may vary if repository conventions require otherwise.

## FE-03: Judge Mode reset

Provide:

- `Run Industrial Emergency`
- `Reset Scenario`
- optional `Run Policy Escalation`
- optional `Run Provider Failure`

Each run must start from a known state.

## FE-04: Live state updates

The timeline should update from real API responses/event stream data, not frontend-only `setTimeout` fiction.

## FE-05: Evidence-first presentation

When an autonomous payment is shown, the screen must first make visible:

```text
Why this payment?

Telemetry: Vibration anomaly
Evidence: historical failure + procedure
Work order: WO-...
Policy: ≤ 500 sats
```

Then show payment.

## FE-06: Proof drawer

Implement full payment proof inspection as described in FR-07.

## FE-07: Vendor comparison

Add quote comparison and selected-vendor explanation.

## FE-08: Economics card

Show estimated business impact only after the underlying scenario has produced the required data.

## FE-09: Accessibility

Add:

- meaningful button labels;
- keyboard focus states;
- readable contrast;
- aria labels for copy/proof controls;
- non-color-only status communication.

## FE-10: Loading/error/empty states

Every API-backed section must have:

- loading;
- empty;
- error;
- success states.

---

# 9. SECURITY REQUIREMENTS

## SEC-01: No secrets in source

Search for:

```bash
grep -RniE 'API[_-]?KEY|SECRET|TOKEN|PASSWORD|ADMIN_KEY|INVOICE_KEY|PRIVATE_KEY' . --exclude-dir=.git --exclude-dir=node_modules
```

Any real secret must be removed and rotated.

## SEC-02: Environment configuration

Use `.env.example` for names only.

Never commit actual Lightning admin or invoice keys.

## SEC-03: Outgoing payment boundary

Outgoing payment capability must remain backend controlled.

## SEC-04: Authorization proof

For every autonomous payment, retain the policy decision and input amount in the audit record.

## SEC-05: Input validation

Validate:

- positive sat amount;
- allowed service IDs;
- bounded confidence;
- work-order identifiers;
- provider/network configuration.

## SEC-06: No accidental live payments in CI

Tests must default to mock/simulation.

CI must not require or invoke production Lightning credentials.

---

# 10. OBSERVABILITY + AUDIT REQUIREMENTS

Every Machine Money execution should have a traceable execution ID.

Minimum audit chain:

```text
execution_id
   ↓
telemetry event
   ↓
evidence selection
   ↓
quote(s)
   ↓
policy decision
   ↓
invoice
   ↓
payment receipt
   ↓
SQL audit record
   ↓
Neo4j payment node
```

The UI should expose the chain in human-readable form.

---

# 11. TEST STRATEGY

All new code must be tested at the closest appropriate layer.

## 11.1 Backend unit tests

Cover:

- QR invoice payload remains exact;
- provider health mode;
- quote generation;
- vendor selection;
- policy within cap;
- policy over cap;
- approval path;
- idempotency;
- SHA-256 proof verification;
- economics calculation;
- execution event schema;
- failure handling.

## 11.2 Backend integration tests

Cover:

- telemetry trigger → quote;
- quote → invoice;
- invoice → policy;
- policy → payment;
- payment → audit;
- payment → graph;
- duplicate trigger;
- provider failure;
- graph unavailable fallback;
- relational persistence.

## 11.3 Frontend unit tests

Cover:

- correct mode badge;
- Judge Mode initial state;
- timeline stage rendering;
- vendor selection rendering;
- economics labels;
- payment proof drawer;
- copy invoice;
- QR component receives exact invoice value;
- failure/empty/loading states.

## 11.4 Frontend E2E tests

At minimum:

### E2E-A: autonomous payment

```text
Open /machine-money
→ click Run Industrial Emergency
→ see telemetry
→ see evidence
→ see policy allowed
→ see invoice/QR
→ see settlement
→ open proof
→ see graph trail
```

### E2E-B: above-cap approval

```text
run policy escalation
→ pending approval
→ approve
→ settlement
→ proof
```

### E2E-C: provider failure

```text
run failure scenario
→ no false settlement
→ visible failure
→ audit remains consistent
```

### E2E-D: duplicate trigger

```text
run same trigger twice
→ one logical settlement
→ duplicate prevention visible
```

### E2E-E: QR scan verification

Use a QR decoding library in a test utility to verify that the generated image encodes the exact BOLT11 payload.

Do not rely only on screenshot inspection.

## 11.5 Regression suites

Existing suite must remain green:

```bash
pytest tests/test_machine_money_task3.py -q
pytest tests/test_machine_money_task4.py -q
pytest tests/test_machine_money_task5.py -q
pytest tests/test_machine_money_task6.py -q
pytest tests/test_e2e_machine_money.py -q
```

Frontend:

```bash
cd frontend
npm test -- --run
npm run lint
npm run build
```

When the dev server is available:

```bash
npm run test:e2e
```

## 11.6 MCP-Driven Verification & Live Inspection Protocol

For each phase touching frontend or data models, use available MCP tools:

1. **`chrome-devtools-mcp`**:
   - `navigate_page`: Load `/machine-money` on local dev server.
   - `list_console_messages` & `get_console_message`: Verify 0 uncaught runtime exceptions or console errors.
   - `take_snapshot` & `take_screenshot`: Capture DOM state and visual proof of timeline, QR code, proof drawer, and economics cards.
   - `list_network_requests`: Inspect API roundtrips for `/api/machine-money/*` routes (status codes, payloads, latency).
   - `click` / `fill`: Execute interactive UI validation directly in the running browser session.

2. **`supabase-mcp-server`**:
   - `execute_sql` / `list_tables`: Audit relational storage and payment logs if Supabase persistence is active.

3. **Phase-Gated Exit Checklist**:
   - Automated tests pass (backend pytest + frontend vitest).
   - MCP live check passes (console clean, network 200 OK, UI renders properly).
   - Git commit created with phase conventional message.
   - User notification & alignment before proceeding to next phase.

---

# 12. VERIFICATION ARTIFACTS

Create and maintain:

- `docs/MACHINE_MONEY_VERIFICATION.md`
- `docs/HACKATHON_ELIGIBILITY.md`
- `docs/JUDGE_DEMO.md`
- `docs/ARCHITECTURE_MACHINE_MONEY.md`
- `docs/MACHINE_MONEY_CHANGELOG.md`

Each should reflect actual behavior, not intended behavior.

The verification document should record:

- test command;
- test count;
- passed/failed;
- environment;
- provider mode;
- deployment URL when available;
- screenshots where appropriate;
- known limitations.

---

# 13. IMPLEMENTATION PHASES

## PHASE 0 — BASELINE, ELIGIBILITY, AND SAFETY GATE

### Task 0.1 — Repository health snapshot

Actions:

- inspect working tree;
- inspect package versions;
- inspect Python version;
- run existing Machine Money test suites;
- record current baseline.

Acceptance:

- baseline status documented;
- no unexplained failures hidden.

Tests:

```bash
pytest tests/test_machine_money_task3.py -q
pytest tests/test_machine_money_task4.py -q
pytest tests/test_machine_money_task5.py -q
pytest tests/test_machine_money_task6.py -q
pytest tests/test_e2e_machine_money.py -q
```

Commit:

```text
chore(hackathon): record machine money baseline
```

### Task 0.2 — Git integrity audit

Actions:

- run the commands in Section 4.3;
- determine actual project history;
- document the earliest relevant commit;
- document eligibility uncertainty instead of assuming.

Acceptance:

`docs/HACKATHON_ELIGIBILITY.md` exists and contains facts, not fabricated dates.

Commit:

```text
docs(hackathon): document repository history and eligibility assumptions
```

### Task 0.3 — Secret and credential audit

Acceptance:

- no real credentials in tracked files;
- `.env.example` contains placeholders only;
- any discovered real credentials are removed and noted for rotation.

Commit:

```text
chore(security): audit machine money credentials
```

---

# PHASE 1 — QR CORRECTNESS + PAYMENT HONESTY

## Task 1.1 — Add standards-compliant QR dependency

Choose a mature QR generation library compatible with Next.js/React and repository constraints.

Acceptance:

- package installed;
- lockfile updated;
- no runtime SSR incompatibility;
- basic rendering test passes.

Commit:

```text
feat(machine-money): add standards-compliant qr encoder
```

## Task 1.2 — Replace pseudo QR

Actions:

- remove `Bolt11QRCode` pseudo-matrix implementation;
- encode the exact invoice string;
- preserve responsive sizing;
- add textual invoice fallback;
- add copy button.

Acceptance:

- QR is scannable;
- no pseudo-grid remains;
- invoice string is exact.

Tests:

- frontend unit;
- QR decode test.

Commit:

```text
fix(machine-money): replace pseudo qr with real invoice encoding
```

## Task 1.3 — Provider mode disclosure

Acceptance:

- `MOCK / SIMULATION` cannot be mistaken for live;
- live provider is clearly indicated;
- provider mode is backend-derived.

Commit:

```text
fix(machine-money): make provider mode explicit in payment ui
```

## Task 1.4 — Proof verification utility

Add a small, reusable verification helper.

Acceptance:

```text
sha256(preimage) == payment_hash
```

is test-covered.

Commit:

```text
feat(machine-money): add payment preimage verification
```

---

# PHASE 2 — JUDGE MODE

## Task 2.1 — Define execution event contract

Add backend schema/model for stage events.

Commit:

```text
feat(machine-money): add structured execution events
```

## Task 2.2 — Build Judge Mode orchestrator endpoint/service

Acceptance:

- one invocation starts the configured demo scenario;
- actual backend services are called;
- no frontend-only fake execution.

Commit:

```text
feat(machine-money): add judge mode orchestration
```

## Task 2.3 — Build execution timeline

Acceptance:

- stages appear from backend events;
- elapsed times are measured;
- errors stop or branch the timeline correctly.

Commit:

```text
feat(machine-money): add live execution timeline
```

## Task 2.4 — Add resettable demo state

Acceptance:

- repeatable runs;
- no stale transaction display;
- reset does not delete unrelated historical payments.

Commit:

```text
feat(machine-money): add repeatable judge scenarios
```

## Task 2.5 — Primary CTA redesign

Make `Run Industrial Emergency` the primary judge action.

Acceptance:

- visible above the fold on desktop;
- obvious on mobile;
- clear loading and completion states.

Commit:

```text
feat(machine-money): add industrial emergency judge mode ui
```

---

# PHASE 3 — EVIDENCE-FIRST PAYMENT FLOW

## Task 3.1 — Evidence summary card

Display why the payment is happening before payment details.

Acceptance:

- telemetry;
- matched evidence;
- work order;
- service;
- confidence;
- policy ID.

Commit:

```text
feat(machine-money): add evidence-first payment rationale
```

## Task 3.2 — Payment proof drawer

Implement full proof package UI.

Commit:

```text
feat(machine-money): add payment proof drawer
```

## Task 3.3 — Proof verification UX

Add `Verify Proof` action.

Acceptance:

- result has an exact source/status;
- mock vs live wording remains accurate.

Commit:

```text
feat(machine-money): expose cryptographic proof verification
```

## Task 3.4 — Graph trail integration in proof drawer

Acceptance:

- one click takes judge from payment proof to operational cause.

Commit:

```text
feat(machine-money): link payment proof to graph trail
```

---

# PHASE 4 — MULTI-VENDOR RFQ

## Task 4.1 — Vendor data model/service

Add deterministic synthetic providers.

Acceptance:

- all data clearly synthetic;
- quote expiry supported.

Commit:

```text
feat(machine-money): add deterministic vendor quote model
```

## Task 4.2 — RFQ API

Return multiple candidates.

Commit:

```text
feat(machine-money): add multi-vendor rfq endpoint
```

## Task 4.3 — Selection logic

Acceptance:

- configurable scoring;
- policy-aware;
- explainable result;
- unit tests for ties and constraints.

Commit:

```text
feat(machine-money): add explainable vendor selection
```

## Task 4.4 — Vendor comparison UI

Commit:

```text
feat(machine-money): add vendor rfq comparison panel
```

---

# PHASE 5 — MACHINE MONEY INTELLIGENCE / INDUSTRIAL ECONOMICS

## Task 5.1 — Metrics model

Implement backend calculations for:

- spend;
- settled;
- pending;
- autonomous count;
- human approvals;
- average settlement latency;
- vendor spend;
- quote-to-payment conversion.

Commit:

```text
feat(machine-money): add machine money analytics metrics
```

## Task 5.2 — Economics model

Implement transparent calculation using synthetic plant assumptions.

Requirements:

- assumptions stored separately;
- versioned calculation;
- `estimated` marker.

Commit:

```text
feat(machine-money): add industrial economics model
```

## Task 5.3 — Analytics dashboard UI

Transform generic activity analytics into Machine Money Intelligence.

Commit:

```text
feat(machine-money): add industrial economics dashboard
```

## Task 5.4 — Explainability drawer for economics

Show the formula/assumption basis.

Commit:

```text
feat(machine-money): explain industrial impact estimates
```

---

# PHASE 6 — POLICY, APPROVAL, AND FAILURE PATH HARDENING

## Task 6.1 — Verify backend policy is authoritative

Acceptance:

- frontend cannot approve a disallowed autonomous payment by itself;
- backend tests cover the boundary.

Commit:

```text
test(machine-money): harden backend policy boundary
```

## Task 6.2 — Improve human approval evidence

Add complete context before approval.

Commit:

```text
feat(machine-money): enrich human approval evidence
```

## Task 6.3 — Provider failure scenario

Acceptance:

- payment remains unsettled;
- no false success toast;
- audit record reflects failure;
- retry guidance is clear.

Commit:

```text
test(machine-money): add provider failure scenario
```

## Task 6.4 — Duplicate trigger scenario

Acceptance:

- one logical settlement;
- same idempotency key visible;
- no duplicate charge.

Commit:

```text
test(machine-money): prove idempotent duplicate trigger handling
```

---

# PHASE 7 — FULL E2E + QR + DEMO REGRESSION

## Task 7.1 — Autonomous happy-path E2E

Implement or extend test for:

```text
trigger
→ evidence
→ rfq
→ policy
→ invoice
→ settlement
→ audit
→ graph
→ economics
```

Commit:

```text
test(machine-money): add complete autonomous lifecycle e2e
```

## Task 7.2 — Above-cap E2E

Commit:

```text
test(machine-money): add policy escalation e2e
```

## Task 7.3 — Provider-failure E2E

Commit:

```text
test(machine-money): add provider failure e2e
```

## Task 7.4 — QR payload regression

Commit:

```text
test(machine-money): verify qr encodes exact bolt11 payload
```

## Task 7.5 — Proof-chain regression

Verify:

```text
payment_hash
preimage
idempotency_key
work_order
predictive_event
policy
graph
sql audit
```

Commit:

```text
test(machine-money): verify complete payment proof chain
```

---

# PHASE 8 — UI POLISH AND JUDGE EXPERIENCE

## Task 8.1 — Above-the-fold optimization

Judge should immediately see:

- what AuRAG does;
- what machine-money action it takes;
- provider mode;
- primary CTA.

Commit:

```text
refactor(machine-money): optimize judge above-fold experience
```

## Task 8.2 — Motion and stage clarity

Use restrained transitions to emphasize state changes.

Do not add motion that hides evidence or delays interaction.

Commit:

```text
feat(machine-money): add execution state transitions
```

## Task 8.3 — Responsive audit

Test desktop/tablet/mobile.

Commit:

```text
fix(machine-money): harden responsive judge layout
```

## Task 8.4 — Accessibility pass

Commit:

```text
fix(machine-money): improve accessibility of payment console
```

---

# PHASE 9 — SECURITY + PRODUCTION-HONESTY PASS

## Task 9.1 — Secret scan

Run source and configuration scans.

Acceptance:

- no secret committed;
- documented key rotation where needed.

Commit:

```text
chore(security): complete pre-submission secret scan
```

## Task 9.2 — Mock/live behavior audit

Inspect every label, toast, metric, receipt, and documentation claim.

Acceptance:

A judge cannot reasonably mistake simulation for live Lightning.

Commit:

```text
fix(machine-money): align mock-live disclosures across ui and docs
```

## Task 9.3 — Error-path audit

Check provider offline, graph offline, bad quote, duplicate trigger, expired invoice, and missing evidence.

Commit:

```text
test(machine-money): complete failure-path audit
```

---

# PHASE 10 — DEPLOYMENT + DEMO OBSERVABILITY

## Task 10.1 — Production build

Run:

```bash
cd frontend
npm run lint
npm run build
```

Backend:

```bash
pytest -q
```

Commit any required fixes:

```text
fix(deploy): resolve production build issues
```

## Task 10.2 — Deployment configuration audit

Verify:

- provider mode;
- environment variables;
- backend URL;
- CORS;
- database connectivity;
- Graph connectivity;
- QR rendering in deployed environment.

Commit:

```text
chore(deploy): verify machine money deployment configuration
```

## Task 10.3 — Health/readiness page

Ensure demo can quickly show system health without leaking secrets.

Commit:

```text
feat(machine-money): add safe system readiness indicators
```

---

# PHASE 11 — DOCUMENTATION, DEMO SCRIPT, AND EVIDENCE PACK

## Task 11.1 — Judge demo script

Create a 3–5 minute script.

Required story:

### 0:00–0:20
Problem: machines can detect an operational event but action still crosses disconnected systems.

### 0:20–0:50
Show AuRAG's graph/evidence layer.

### 0:50–2:10
Run Industrial Emergency.

### 2:10–2:50
Show policy and payment proof.

### 2:50–3:30
Show graph trail and vendor/economic outcome.

### 3:30–4:00
Show human-in-the-loop escalation for the above-cap case.

### 4:00–5:00
Summarize technical architecture and proof.

Commit:

```text
docs(hackathon): add judge demo script
```

## Task 11.2 — Verification report

Record actual test outputs and deployment status.

Commit:

```text
docs(hackathon): add machine money verification report
```

## Task 11.3 — Eligibility report

Record:

- source project history;
- event rules reviewed;
- code reuse decisions;
- any organizer clarification;
- final compliance status.

Commit:

```text
docs(hackathon): finalize eligibility and provenance record
```

## Task 11.4 — Final changelog

Document each major change using real commit dates.

Commit:

```text
docs(hackathon): publish implementation changelog
```

---

# 14. FINAL ACCEPTANCE CHECKLIST

## Core Machine Money

- [ ] Telemetry trigger works.
- [ ] Evidence is grounded and inspectable.
- [ ] Vendor quote is generated.
- [ ] Multi-vendor RFQ works.
- [ ] Policy gate is backend-authoritative.
- [ ] Autonomous payment works in supported mode.
- [ ] Human approval works.
- [ ] BOLT11 invoice is generated.
- [ ] QR is standards-compliant and decodes to the exact invoice.
- [ ] Payment proof is inspectable.
- [ ] Preimage/hash verification works when available.
- [ ] Idempotency prevents duplicates.
- [ ] SQL audit persists.
- [ ] Neo4j graph trail persists.
- [ ] Provider failures do not create false settlements.

## Judge Experience

- [ ] Judge Mode works from one obvious CTA.
- [ ] Timeline is understandable without narration.
- [ ] Provider mode is obvious.
- [ ] Why/what/how much/where/outcome are all visible.
- [ ] Proof drawer opens cleanly.
- [ ] Vendor selection is explainable.
- [ ] Industrial economics is visibly labelled as estimated/synthetic where applicable.
- [ ] Mobile view is usable.

## Quality

- [ ] Backend tests pass.
- [ ] Frontend tests pass.
- [ ] E2E tests pass.
- [ ] QR decoding test passes.
- [ ] Production build passes.
- [ ] Secret scan passes.
- [ ] Documentation matches actual behavior.

## Provenance / Eligibility

- [ ] Actual Git history was inspected.
- [ ] No timestamps were fabricated.
- [ ] No fake historical commits were created.
- [ ] No real credentials were committed.
- [ ] LightningTime reuse is limited to allowed patterns/code under the event rules.
- [ ] Any prior-project reuse is disclosed where the rules or organizer require it.

---

# 15. FINAL DEMO SCENARIOS

## Scenario 1 — Autonomous machine payment

Input:

```text
Equipment: P-101A
Telemetry: vibration 5.8 mm/s
Confidence: 94%
Service: bearing inspection
Quote: 250 sats
Cap: 500 sats
```

Expected:

```text
Telemetry detected
→ evidence matched
→ quote selected
→ policy allowed
→ invoice created
→ payment settled
→ proof verified
→ work order funded
→ graph/audit linked
```

## Scenario 2 — Human approval

Input:

```text
Service: motor rewind
Quote: 1,200 sats
Cap: 500 sats
```

Expected:

```text
Policy: exceeds autonomous cap
→ PENDING_APPROVAL
→ operator reviews evidence
→ operator approves
→ payment settles
→ audit records approval
```

## Scenario 3 — Duplicate event

Input:

Run Scenario 1 twice with the same logical event key.

Expected:

```text
One logical payment
No duplicate settlement
Existing record returned/reused
```

## Scenario 4 — Provider failure

Expected:

```text
Payment attempt fails
→ FAILED
→ no false settlement
→ audit remains accurate
→ retry guidance shown
```

---

# 16. DESIGN PRINCIPLES FOR THE FINAL PRODUCT

1. **Show causality, not just transactions.**
2. **Show evidence before money.**
3. **Make policy visible.**
4. **Make provider mode explicit.**
5. **Use a real QR code.**
6. **Make every business-impact number traceable to assumptions.**
7. **Keep the backend authoritative.**
8. **Use LightningTime's product lessons as patterns, not as a cloned feature set.**
9. **Prefer one compelling end-to-end flow over many shallow features.**
10. **Preserve an honest, auditable development history.**

---

# 17. AGENT RESPONSE CONTRACT

After each task, respond with exactly this structure:

```text
TASK: <task id + title>
STATUS: PASS | BLOCKED | FAILED

CHANGES:
- <file>: <what changed>

TESTS:
- <command>: PASS/FAIL

REGRESSION:
- <command>: PASS/FAIL

COMMIT:
- <hash> <message>

RISKS / FOLLOW-UP:
- <only real remaining issue>
```

If a test fails, do not create a green-looking completion report. Fix the failure or report the task as `BLOCKED` / `FAILED` with the exact reason.

---

# 18. STOP CONDITIONS

The agent must stop and ask the user before continuing when:

- an event rule materially prohibits reuse of the existing implementation;
- a live Lightning credential is required but not safely available through environment configuration;
- a production payment could be triggered accidentally;
- a change would require rewriting public Git history;
- required external credentials or services are unavailable;
- an acceptance criterion conflicts with factual behavior and cannot be implemented honestly.

---

# 19. PRIORITY ORDER WHEN TIME IS LIMITED

Do not sacrifice correctness for feature count.

Priority order:

```text
P0  Eligibility / provenance / secrets / QR correctness
P0  Judge Mode end-to-end lifecycle
P0  Evidence + policy + payment proof
P1  Multi-vendor RFQ
P1  Industrial Economics
P1  Failure + duplicate scenarios
P1  Full E2E regression
P2  Visual polish
P2  Deployment polish
P2  Documentation polish
```

A smaller system that truthfully completes the full machine-money causal chain is preferable to a larger system with fake, disconnected, or untestable features.

---

# 20. END STATE

The finished AuRAG Machine Money product should let a judge see, in one continuous flow:

> **A machine generated a signal. AuRAG understood the operational context. GraphRAG supplied evidence. A vendor/service action was selected. A spending policy decided whether money could move. Lightning settled the authorized amount. The proof was recorded. The payment was linked to the work order and the machine event. The system explained the industrial outcome.**

That is the complete product story this PRD is intended to build.
