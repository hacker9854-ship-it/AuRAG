# PRD — AuRAG Final Hackathon Hardening & Submission Plan

**Project:** AuRAG — Autonomous Industrial Intelligence + Machine Money  
**Track:** Machine Money  
**Objective:** Maximize judge-visible technical depth, factual credibility, demo reliability, and product clarity before final submission.

> This PRD is an execution document. Every phase has a deliverable, exact acceptance criteria, tests, and a required commit. Do not start the next phase until the current phase passes its gate.

---

# 0. Non-Negotiable Rules

## 0.1 Truthfulness

The repository, README, UI, screenshots, demo script, and submission form must describe the implementation exactly.

Never:
- backdate or rewrite Git history to fabricate development duration
- claim a live Lightning settlement when the demo is simulated
- claim BOLT11 compliance when the payload is not a valid BOLT11 invoice
- claim GraphRAG retrieval when the executed demo path only uses a fixture
- claim real vendor APIs when vendors are synthetic/pre-approved
- claim measured production performance from mock/local execution
- present synthetic economics as real losses avoided
- claim unsupported “first”, “industry-grade”, “unforgeable”, “production-grade” status

Use explicit labels:
- `MOCK / SIMULATION`
- `CONTROLLED DEMO FIXTURE`
- `SYNTHETIC DATA`
- `MODELLED ECONOMICS`
- `LIVE LIGHTNING` only when the provider is actually live

## 0.2 Scope discipline

Do not add another major framework, database, blockchain, or agent system after Phase 2 unless it directly fixes a blocker.

The final product should feel like one coherent system:

> **Detect → Ground → Decide → Quote → Govern → Pay → Prove → Act**

## 0.3 Canonical scenario

Use one canonical judge scenario everywhere:

- Equipment: `P-101A`
- Sensor: `VIB-301-BEARING`
- Vibration: `5.4 mm/s`
- Threshold: `4.5 mm/s`
- Service: `bearing-inspection`
- Autonomous payment: `250 sats`
- Autonomous cap: `500 sats`
- Escalation scenario: `1,200 sats`
- Vendors: exactly `3`
- Failure evidence: `FE-001`
- Historical work order: `WO-1002`
- Procedure: `PROC-001`
- Economics: `4.5h` modelled outage, `$1.17M` modelled exposure
- Economics ratio for 250 sats: `7,800,000:1` modelled protection multiple

No other amount/vendor count should appear in the primary README/demo unless clearly marked as a separate test case.

---

# 1. Current Audit Findings

The latest repository is already strong in architecture and product presentation. The remaining blockers are mostly credibility/consistency issues.

## P0 blockers

### P0-1. Mock provider emits a “realistic-looking” string, not a standards-valid BOLT11 invoice

Current file:
`backend/app/services/machine_money/providers/mock.py`

The mock provider manually constructs a string beginning with `lnbcrt...`, but the payload is not actually produced by BOLT11 encoding/signing.

### P0-2. Judge Mode labels Stage 2 as GraphRAG, but the current `build_operational_evidence_package()` path is deterministic

Current files:
- `backend/app/services/machine_money/service.py`
- `backend/app/services/machine_money/bridge.py`

`build_operational_evidence_package()` currently returns deterministic references such as:
`FE-001`, `WO-1002`, `PROC-001`.

The repository contains a real hybrid retrieval implementation in:
`retrieval/hybrid.py`

The final Judge Mode must either:
1. call that real retrieval path, or
2. explicitly label the evidence as a controlled demo fixture.

Preferred solution: wire real retrieval with a deterministic fallback that remains honestly labeled.

### P0-3. README still contains a few claims that are broader than the implementation

Examples to remove/rewrite:
- “first industrial-grade implementation”
- “vendor APIs” when the current demo uses synthetic vendors
- “sub-second finality” as a general production claim
- “unforgeable audit evidence”
- generic statements implying mainnet settlement when the deployment is mock

### P0-4. README has consistency risk

Canonical values must be normalized:
- payment amount: 250 sats
- vendor count: 3
- economics ratio: 7,800,000:1
- test count: determined by the final verified CI run, not hardcoded from stale documentation

### P0-5. Mock/live and proof semantics must be separated

In mock mode:
`SHA256(preimage) == payment_hash`

means the simulation is internally cryptographically consistent.

It does NOT mean that a real Lightning network payment was settled.

UI and docs must distinguish:
- `Simulation integrity proof`
- `Live Lightning settlement proof`

---

# 2. Final Product Contract

## 2.1 The product story

AuRAG is not “an AI app that pays with Bitcoin.”

The product story is:

> An industrial intelligence system turns a grounded machine event into a governed financial action, settles the action over a pluggable Lightning interface, and preserves the causal evidence linking the machine event to the payment.

The complete chain:

```text
SCADA telemetry
      ↓
Anomaly detection
      ↓
Grounded evidence retrieval
      ↓
Failure diagnosis
      ↓
Service selection
      ↓
3-vendor RFQ
      ↓
Policy / budget gate
      ↓
BOLT11 invoice
      ↓
Lightning settlement
      ↓
Payment proof
      ↓
Audit + graph lineage
      ↓
Operational outcome
```

## 2.2 Judge mental model

A judge should be able to answer these five questions within seconds:

1. Why did the machine need to spend money?
2. What evidence justified the action?
3. Why was the amount allowed?
4. How was the payment executed?
5. What proof links the payment back to the industrial event?

---

# 3. Phase 0 — Baseline Freeze & Audit

## Goal

Create one authoritative baseline before modifying functionality.

## Tasks

### 0.1 Record repository baseline

Record:
- current branch
- current HEAD
- current README SHA
- current test snapshot
- deployment URLs
- current environment mode
- current screenshots list

Do not modify historical commits.

### 0.2 Run the actual test suite

Backend:

```powershell
.\.venv\Scripts\pytest.exe -q
```

Frontend:

```powershell
cd frontend
npm ci
npm test -- --run
npm run lint
npm run build
```

Browser:

```powershell
npm run test:e2e
```

### 0.3 Save one canonical snapshot

Create/update:
`docs/CURRENT_TEST_SNAPSHOT.md`

It must contain:
- exact commands
- exact timestamps of the verification run
- exact test counts
- exact pass/fail result
- build result
- lint result
- E2E result

Do not manually type a test count that was not produced by the run.

### 0.4 Documentation link audit

Check every relative README link with a script.

Acceptance:
- no broken internal links
- no references to deleted files
- no stale filenames such as `PRD2.md` where the actual file differs

### 0.5 Claims audit

Create:
`docs/CLAIM_EVIDENCE_MATRIX.md`

Columns:

| Claim | Evidence file | Evidence test | Current environment | Allowed wording |
|---|---|---|---|---|

Every material technical claim in README must have an evidence row.

### Phase 0 Gate

PASS only if:
- baseline test results are captured from a real run
- all README links resolve
- every major claim has evidence
- no Git history manipulation is performed

### Commit

```text
chore(submission): freeze baseline verification and claim evidence
```

---

# 4. Phase 1 — Make Mock Payment Protocol-Sound

## Goal

Remove the biggest Machine Money credibility hole.

## 1.1 Add a standards-compliant BOLT11 library

Preferred backend dependency:

`bolt11==2.2.0`

The package implements Lightning BOLT11 encoding/decoding and supports Python 3.10–3.12.

Reference:
- BOLT #11 specification: https://github.com/lightning/bolts/blob/master/11-payment-encoding.md
- Python package: https://pypi.org/project/bolt11/2.2.0/

Do NOT hand-roll Bech32/BOLT11.

## 1.2 Replace mock invoice construction

File:
`backend/app/services/machine_money/providers/mock.py`

Replace manual string construction with actual library encoding.

Requirements:
- correct network prefix
- exact amount
- timestamp
- payment hash
- payment secret
- description
- expiry
- valid signature
- valid checksum

Use an ephemeral/test-only signing key generated at runtime for the mock provider.

Do not commit a reusable private key.

## 1.3 Validate the invoice immediately after encoding

The provider must internally:

```text
encode → decode → verify fields
```

Acceptance:
- decoded amount matches request
- decoded payment hash matches stored payment hash
- payment hash equals SHA256(preimage)
- network matches configured mock network
- invoice expires according to requested expiry
- invalid invoice causes a test failure

## 1.4 Reject arbitrary malformed invoices in mock mode

Current behavior for unknown/ad-hoc invoice strings must not silently create a default 150-sat payment.

Remove that behavior.

Required behavior:

```text
unknown invoice
    ↓
BOLT11 decode fails
    ↓
ProviderError
    ↓
0 sats deducted
```

## 1.5 Frontend invoice verification

The UI should not only check the prefix.

Preferred behavior:
- QR decoder verifies QR content
- BOLT11 parser validates the invoice
- UI extracts amount/network/payment hash
- UI compares displayed amount to expected amount

If browser-side full BOLT11 parsing introduces unnecessary dependency complexity, backend must expose a verified parsed invoice object and frontend must clearly show `Backend-Verified BOLT11`.

## 1.6 QR test matrix

Add tests for:

```text
mainnet
testnet
signet
regtest
```

Test:

```text
invoice → QR → image decode → exact invoice string
invoice → BOLT11 decode → exact amount/payment hash/network
```

### Phase 1 Gate

A judge should be able to scan/copy the simulated invoice and the application must either:
- parse it as a valid BOLT11 invoice, or
- clearly state that the current artifact is not a payment-ready Lightning invoice.

Preferred final state: valid BOLT11.

### Commit

```text
fix(machine-money): generate standards-valid bolt11 mock invoices
```

---

# 5. Phase 2 — Ground the Judge Mode in Actual Retrieval

## Goal

Remove the “fake GraphRAG stage” risk.

## 2.1 Create a grounded evidence service

Create:

`backend/app/services/machine_money/grounding.py`

Responsibilities:
- accept telemetry event
- formulate deterministic query
- call `retrieval.hybrid.retrieve(...)`
- collect top evidence
- optionally call `retrieval.graph_traversal.traverse(...)`
- map results into the Machine Money evidence contract
- return:
  - evidence IDs
  - text snippets
  - retrieval scores
  - source types
  - equipment anchor
  - failure event
  - work order
  - procedure
  - retrieval method

## 2.2 Deterministic query construction

For canonical Judge Mode:

```text
Why did P-101A trigger an intervention after vibration reached
5.4 mm/s against a 4.5 mm/s threshold?
```

The query must be grounded in actual event inputs.

Do not inject `FE-001`, `WO-1002`, `PROC-001` as hidden hardcoded “answers” into the retrieval function.

## 2.3 Retrieval evidence contract

Minimum output:

```json
{
  "source": "HYBRID_RETRIEVAL",
  "equipment": "P-101A",
  "evidence": [
    {
      "id": "FE-001",
      "type": "FailureEvent",
      "score": 0.94,
      "reason": "..."
    },
    {
      "id": "WO-1002",
      "type": "WorkOrder",
      "score": 0.88,
      "reason": "..."
    },
    {
      "id": "PROC-001",
      "type": "Procedure",
      "score": 0.84,
      "reason": "..."
    }
  ]
}
```

## 2.4 Controlled fallback

If Neo4j/Qdrant/reranker is unavailable:

```text
REAL RETRIEVAL UNAVAILABLE
        ↓
CONTROLLED DEMO FIXTURE
```

The UI must display:

`CONTROLLED DEMO FIXTURE`

not:

`GraphRAG Retrieved`

This preserves demo reliability without misrepresenting the source.

## 2.5 Confidence gate

Define:

```text
confidence < 0.75
    → PENDING_APPROVAL

confidence >= 0.75
    → continue policy evaluation
```

Use the same rule in docs, code, tests, and UI.

### Phase 2 Gate

Judge Mode must use:
- real retrieval when infrastructure is available
- explicit fixture label when fallback is used
- no hidden hardcoded evidence claim

### Commit

```text
feat(machine-money): ground judge mode in hybrid graph retrieval
```

---

# 6. Phase 3 — Strengthen the Causal Evidence Chain

## Goal

Make the strongest part of AuRAG visually undeniable.

## 3.1 Canonical evidence graph

The final causal chain:

```text
Equipment
   ↓
PredictiveEvent
   ↓
FailureSignature
   ↓
WorkOrder
   ↓
ServiceQuote
   ↓
PolicyDecision
   ↓
Payment
   ↓
ServiceProvider
```

## 3.2 Every payment must store causal references

Payment metadata should contain:

- equipment ID
- sensor ID
- predictive event ID
- failure event ID
- work order ID
- quote ID
- vendor ID
- policy decision ID
- idempotency key
- invoice ID
- payment hash
- preimage
- provider mode
- settlement source
- evidence source

## 3.3 Proof drawer redesign

Tabs:

1. `Why We Paid`
2. `RFQ Decision`
3. `Policy Decision`
4. `Lightning Proof`
5. `Graph Lineage`
6. `Audit Ledger`

Top banner:

```text
PAYMENT STATUS
MOCK / SIMULATION
```

or

```text
PAYMENT STATUS
LIVE LIGHTNING
```

Never show both.

## 3.4 Proof semantics

In simulation:

```text
SHA256(preimage) == payment_hash
```

label:

`Simulation integrity check`

In live mode:

```text
Provider reports settlement
+
invoice/payment hash
+
preimage
```

label:

`Provider-reported Lightning settlement evidence`

### Phase 3 Gate

A judge can answer:

> Why did this payment happen?

by reading one drawer without opening source code.

### Commit

```text
feat(machine-money): strengthen causal payment evidence chain
```

---

# 7. Phase 4 — Finalize Judge Mode

## Goal

Turn the entire platform into a reliable 60–90 second demonstration.

## 4.1 Exactly three scenarios

### Scenario A — Autonomous Intervention

Input:
- P-101A
- 5.4 mm/s
- 250 sats

Flow:

```text
Detect
→ Retrieve
→ Diagnose
→ RFQ
→ Policy PASS
→ Invoice
→ Settlement
→ Proof
```

### Scenario B — Human Escalation

Input:
- same evidence
- 1,200 sats

Flow:

```text
Detect
→ Retrieve
→ Diagnose
→ RFQ
→ Policy FAIL
→ PENDING_APPROVAL
```

Then operator approval:

```text
Approve
→ Invoice
→ Settlement
→ Proof
```

### Scenario C — Provider Failure

Input:
- 250 sats

Flow:

```text
Detect
→ Retrieve
→ Diagnose
→ RFQ
→ Policy PASS
→ Invoice
→ Provider FAILURE
→ 0 sats lost
→ Retry guidance
```

## 4.2 Execution timeline

Use exactly these stages:

```text
01 ANOMALY_DETECTED
02 EVIDENCE_MATCHED
03 FAILURE_DIAGNOSED
04 QUOTE_RESOLVED
05 POLICY_AUTHORIZED
06 INVOICE_CREATED
07 PAYMENT_SETTLED
08 GRAPH_COMMITTED
09 OPERATIONAL_OUTCOME
```

Failure path must stop at the correct stage.

## 4.3 Timing labels

Show:

`Measured demo execution time`

Do not show:
`Lightning network finality`

unless the live provider actually measured it.

## 4.4 One primary CTA

Primary:

`RUN INDUSTRIAL EMERGENCY`

Secondary:
- `POLICY ESCALATE`
- `PROVIDER FAILURE`

No unnecessary controls above the fold.

## 4.5 Recovery

Every scenario must have:

`RESET DEMO`

and the reset must clear:
- timeline
- active payment
- stale evidence
- toasts
- previous modal state
- selected proof ID

### Phase 4 Gate

A fresh browser session must run each scenario without manual database cleanup.

### Commit

```text
feat(machine-money): finalize deterministic judge scenarios
```

---

# 8. Phase 5 — RFQ & Vendor Decision Quality

## Goal

Make multi-vendor selection useful instead of decorative.

## 5.1 Exactly three synthetic vendors

Canonical vendors:

- Apex Diagnostics
- Precision Dynamics
- Quantum Reliability

Always label:

`Synthetic / Pre-approved vendor nodes`

## 5.2 Score must be deterministic and explainable

Canonical formula:

```text
BalancedScore =
  0.50 × normalized_cost
+ 0.30 × normalized_latency
+ 0.20 × normalized_reliability
```

Document the normalization.

## 5.3 RFQ output must bind to payment

The selected quote must produce:

```text
quote_id
→ vendor_id
→ amount_sats
→ service_id
→ work_order_id
→ invoice_id
→ payment_id
```

No payment may exist without a quote reference.

## 5.4 UI

Show:
- vendor
- cost
- SLA
- reliability
- selected strategy
- final score
- reason for selection

### Gate

One vendor must be selected deterministically for the canonical scenario.

### Commit

```text
fix(machine-money): bind rfq decision to settlement proof
```

---

# 9. Phase 6 — Industrial Economics Cleanup

## Goal

Make the business value compelling without exaggeration.

## 6.1 Canonical model

```text
Avoided exposure =
    avoided downtime hours × hourly exposure rate
```

Canonical model:
- 4.5h
- $260,000/hour assumption if used
- $1.17M modelled exposure

## 6.2 Cost

250 sats must be converted using a clearly disclosed conversion input.

If USD conversion is shown:
- display the exchange-rate assumption
- show timestamp/source when the value is dynamic
- never imply the sat/USD rate is static

## 6.3 Language

Use:

`$1.17M modelled downtime exposure`

Not:

`$1.17M loss prevented`

Use:

`7,800,000:1 modelled protection multiple`

Not:

`7.8M ROI guaranteed`

## 6.4 Sensitivity sandbox

Allow judges to modify:
- outage hours
- hourly exposure
- intervention cost

Clearly mark outputs:

`MODELLED`

### Commit

```text
fix(machine-money): normalize economics assumptions and disclosures
```

---

# 10. Phase 7 — System Readiness Correctness

## Goal

Never show placeholder values as live operational health.

## 10.1 No fake defaults

Current examples such as:
- `1.2 ms`
- `1,000,000 sats`
- `ALL SYSTEMS NOMINAL`

must not appear when the backend did not report them.

Fallback state must be:

```text
UNKNOWN
Not reported
```

## 10.2 Mode-aware status

When mock:

```text
Lightning Provider
MOCK / SIMULATION
```

When live:

```text
Lightning Provider
LIVE
```

## 10.3 Security panel

Do not claim:

`0 Secrets in Memory`

based only on the browser rendering.

Instead say:

`No credentials exposed by readiness endpoint`

and back it with a server-side sanitized DTO.

### Commit

```text
fix(machine-money): make readiness status evidence-backed
```

---

# 11. Phase 8 — README Final Rewrite

## Goal

The README must sell the system in the first 30 seconds and support technical verification afterward.

## 11.1 New README structure

Use this exact top-level order:

```text
1. AuRAG title + one-line thesis
2. Live Demo / Repo / Demo Video
3. 30-second explanation
4. The Machine Money loop
5. What is live today
6. Golden-path screenshots
7. 60-second judge walkthrough
8. Why Lightning for this use case
9. Governance & policy
10. Proof / audit trail
11. Architecture
12. RFQ
13. Industrial economics
14. Testing
15. Setup
16. Deep technical documentation links
17. FAQ
18. License / credits
```

## 11.2 New opening copy

Recommended:

> **AuRAG is an industrial intelligence system that turns a grounded machine event into a governed financial action. It retrieves operational evidence, selects a service provider, enforces spending policy, settles a micro-payment through a pluggable Lightning provider, and preserves the causal evidence linking the machine event to the payment.**

## 11.3 Remove weak/unsupported language

Delete:
- “first industrial-grade”
- “industry-grade”
- “unforgeable”
- “loss averted”
- “vendor APIs” unless actually connected
- generic “sub-second finality” claims

## 11.4 Replace with precise language

Use:
- `standards-valid BOLT11 invoice` only after Phase 1 passes
- `synthetic vendor RFQ`
- `modelled exposure`
- `measured demo execution time`
- `provider-reported live settlement`
- `simulation integrity proof`
- `hybrid retrieval evidence`

## 11.5 What is live today table

Mandatory:

| Subsystem | Current demo | Production target |
|---|---|---|
| Frontend | Live Vercel deployment | Same |
| Backend | Live deployment | Same |
| Machine Money | Live workflow | Same |
| Lightning | Mock / Simulation unless live provider configured | LNbits/CLN/LND |
| RFQ | 3 synthetic providers | External provider federation |
| Economics | Synthetic/modelled plant scenario | Real plant telemetry + calibrated model |
| GraphRAG | Real retrieval when dependencies available | Production graph/retrieval stack |

## 11.6 Test claims

Do not hardcode:

`136 / 136`

unless the latest authoritative run actually reports 136.

README should link to:
`docs/CURRENT_TEST_SNAPSHOT.md`

and say:

> **Automated test suites verified in CI; see the current verification snapshot for the exact run.**

## 11.7 FAQ corrections

Mandatory FAQ:

### Is this live Bitcoin mainnet?

Answer:
No, unless a live provider is configured. The public demo is explicitly labeled `MOCK / SIMULATION`.

### Is the mock invoice a valid BOLT11 invoice?

Answer:
Yes only after Phase 1 passes the BOLT11 decode/signature tests. Otherwise do not claim this.

### Is the industrial data real?

Answer:
Operational plant data is synthetic/modelled for demonstration.

### Does Judge Mode use real GraphRAG?

Answer:
Yes when configured dependencies are available. Otherwise the system explicitly labels a controlled demo fixture fallback.

---

# 12. Phase 9 — Screenshot & Visual Evidence Pack

## Required screenshots

Use seven strong screenshots, not many repetitive ones.

### Screenshot 1
`machine-money-above-fold.png`

Must show:
- Judge Mode
- `250 sats`
- simulation/live badge
- 500-sat policy
- business impact

### Screenshot 2
`machine-money-execution-timeline.png`

Must show populated execution stages.

### Screenshot 3
`machine-money-rfq.png`

Must show all three vendors and final selection.

### Screenshot 4
`machine-money-policy-escalation.png`

Must show:
`1,200 sats`
→ `PENDING_APPROVAL`

### Screenshot 5
`machine-money-proof-drawer.png`

Must show:
- payment hash
- preimage verification
- invoice parsing
- graph lineage
- mode disclosure

### Screenshot 6
`machine-money-provider-failure.png`

Must show:
- provider error
- zero funds lost
- remediation

### Screenshot 7
`machine-money-economics.png`

Must show:
- modelled exposure
- assumptions
- formula
- sensitivity

## Screenshot integrity

Each image must correspond to the current UI.

Do not keep stale screenshots after UI changes.

### Commit

```text
docs(machine-money): refresh judge evidence screenshots
```

---

# 13. Phase 10 — Full E2E Verification

## 13.1 Backend tests

Must cover:

### Protocol
- BOLT11 encoding
- BOLT11 decoding
- amount preservation
- network preservation
- payment hash preservation
- expiry
- malformed invoice rejection

### Governance
- 500 sats passes
- 501 sats escalates
- 1,200 sats escalates
- daily budget ceiling
- client bypass rejected
- approval settles successfully

### Idempotency
- duplicate happy-path trigger
- duplicate pending-approval trigger
- retry after provider failure
- zero duplicate charges

### Failure
- provider offline
- malformed quote
- invoice expired
- graph unavailable
- retrieval unavailable
- low-confidence evidence

### Evidence
- causal chain completeness
- quote/payment binding
- proof package completeness
- mode disclosure

## 13.2 Frontend tests

Must cover:
- Judge Mode
- all three scenarios
- timeline
- RFQ
- policy escalation
- proof drawer
- BOLT11 UI validation
- QR round-trip
- mode badge
- readiness modal
- economics disclosure

## 13.3 Browser E2E

Run:

```powershell
cd frontend
npm run test:e2e
```

At minimum automate:

```text
open Machine Money
run happy path
verify final state
open proof drawer
verify mode label
run policy scenario
verify pending approval
approve
verify settlement
reset
run failure scenario
verify failed state
verify 0-sat loss
```

---

# 14. Phase 11 — CI / Reproducibility

## Goal

A judge should be able to reproduce core quality signals.

CI must run:

```text
Backend pytest
Frontend Vitest
Frontend lint
Frontend build
Playwright
Docker config validation
Secret scan
```

## 14.1 Secret handling

- `.env` ignored
- no tokens in tracked files
- no wallet private keys committed
- runtime-generated mock signing keys
- no browser-exposed wallet admin credentials
- server-only secrets for live provider

## 14.2 CI truthfulness

Badge values should be generated from CI where practical.

Do not use a manually updated green badge to imply tests passed if they did not.

### Commit

```text
chore(ci): enforce final machine money verification gates
```

---

# 15. Phase 12 — Final README Claim Audit

Run a simple text audit for:

```text
first
industrial-grade
production-grade
unforgeable
mainnet
sub-second
vendor API
real vendors
loss prevented
guaranteed
```

Every occurrence must be reviewed.

Allowed only when technically justified.

Also search for inconsistent canonical values:

```text
50 sats
250 sats
500 sats
1200 sats
3 vendors
4 vendors
7.2M
7.8M
```

Primary README must contain only the canonical numbers except where a scenario table explicitly explains the alternative.

---

# 16. Phase 13 — Demo Story

## 0:00–0:15 — Problem

> “A machine can know it is failing and still wait for humans to approve the operational action.”

Show P-101A anomaly.

## 0:15–0:30 — Evidence

Run:

`RUN INDUSTRIAL EMERGENCY`

Show:
- telemetry
- hybrid retrieval
- failure evidence

Say:

> “AuRAG does not authorize spending from the sensor alone. The event must be grounded in operational evidence.”

## 0:30–0:50 — RFQ

Show three vendors.

Say:

> “The system compares pre-approved service nodes using cost, SLA and reliability.”

## 0:50–1:05 — Governance

Show 250 sats against 500-sat cap.

Say:

> “The financial boundary is enforced server-side. The agent cannot override it.”

## 1:05–1:20 — Payment

Show:
- BOLT11 invoice
- QR
- settlement state
- proof

Say:

> “The payment is bound to the quote, work order and event.”

## 1:20–1:35 — Proof

Open proof drawer.

Show causal chain.

Say:

> “The question is not only ‘did we pay?’ It is ‘why did we pay?’”

## 1:35–1:50 — Escalation

Run 1,200-sat scenario.

Show:
`PENDING_APPROVAL`

Say:

> “Above policy, autonomy stops.”

## 1:50–2:00 — Close

> “AuRAG turns machine intelligence into a governed operational action with an auditable payment trail.”

---

# 17. What NOT to Do

Do not:
- add unrelated features
- add another LLM just for a badge
- add fake blockchain records
- fabricate vendor responses
- fabricate Lightning network settlement
- backdate commits
- rewrite old history
- add hundreds of meaningless commits
- hide the simulation label
- inflate economics
- add unsupported benchmark claims
- call synthetic telemetry “real SCADA”
- call deterministic fixture retrieval “live GraphRAG”
- use a QR image that cannot be decoded

---

# 18. Git / Provenance Policy

Historical commits must remain untouched.

Do not use:
- `git filter-branch`
- `git filter-repo` to alter timestamps
- mass amend operations
- artificial commit backdating
- fake author identities

Continue development with genuine commits.

A clean, truthful history is safer than a fabricated 15-day timeline.

The goal is to make the current codebase verifiably strong, not to manufacture a story about when it was built.

---

# 19. Final Submission Checklist

## Product

- [ ] happy path works from fresh browser
- [ ] policy escalation works
- [ ] provider failure works
- [ ] reset works
- [ ] no stale state
- [ ] no console errors
- [ ] no broken route
- [ ] mobile layout works

## Machine Money

- [ ] valid BOLT11 mock invoice
- [ ] BOLT11 decode test
- [ ] QR round-trip test
- [ ] payment hash check
- [ ] preimage consistency check
- [ ] live/mock disclosure
- [ ] no arbitrary malformed invoice payment
- [ ] idempotency
- [ ] spending cap
- [ ] daily budget
- [ ] approval flow
- [ ] failure path

## GraphRAG

- [ ] real retrieval path connected
- [ ] controlled fixture fallback labeled
- [ ] evidence IDs grounded
- [ ] source scores available
- [ ] causal chain stored

## RFQ

- [ ] 3 vendors exactly
- [ ] synthetic disclosure
- [ ] deterministic scoring
- [ ] selected quote bound to payment

## Economics

- [ ] modelled label
- [ ] assumptions visible
- [ ] formula visible
- [ ] no “loss prevented” claim
- [ ] canonical 250-sat scenario

## README

- [ ] first 30 seconds understandable
- [ ] current/live status clear
- [ ] all screenshots fresh
- [ ] no unsupported claims
- [ ] test count links to current snapshot
- [ ] no stale values
- [ ] links checked

## Submission

- [ ] repository public
- [ ] live demo works
- [ ] demo video works
- [ ] submission text matches README
- [ ] no secret credentials
- [ ] provenance truthful
- [ ] final commit pushed
- [ ] final tag created if desired

---

# 20. Final Release Gate

The project is **submission-ready only when all of the following are true**:

```text
[PASS] BOLT11 protocol correctness
[PASS] QR round-trip
[PASS] Grounded GraphRAG evidence
[PASS] Controlled fixture disclosure
[PASS] RFQ-to-payment binding
[PASS] Policy enforcement
[PASS] Idempotency
[PASS] Failure handling
[PASS] Proof chain
[PASS] Economics disclosure
[PASS] README claim audit
[PASS] Screenshot freshness
[PASS] Full automated test run
[PASS] Browser E2E run
[PASS] Secret scan
[PASS] Deployment smoke test
[PASS] Final demo rehearsal
```

If any P0 gate fails, do not freeze the submission.

---

# 21. Required Commit Sequence

Execute in this order:

```text
1. chore(submission): freeze baseline verification and claim evidence
2. fix(machine-money): generate standards-valid bolt11 mock invoices
3. feat(machine-money): ground judge mode in hybrid graph retrieval
4. feat(machine-money): strengthen causal payment evidence chain
5. feat(machine-money): finalize deterministic judge scenarios
6. fix(machine-money): bind rfq decision to settlement proof
7. fix(machine-money): normalize economics assumptions and disclosures
8. fix(machine-money): make readiness status evidence-backed
9. docs(machine-money): refresh judge evidence screenshots
10. chore(ci): enforce final machine money verification gates
11. docs(submission): finalize README and claim evidence matrix
12. chore(release): finalize hackathon submission package
```

After every commit:

```powershell
git status
git diff --check
```

Then run the smallest relevant test suite.

Before release:

```powershell
.\.venv\Scripts\pytest.exe -q
cd frontend
npm test -- --run
npm run lint
npm run build
npm run test:e2e
```

---

# 22. Definition of Done

AuRAG is done when the judge can see, in one coherent flow:

```text
A MACHINE HAD A PROBLEM
        ↓
WE GROUNDED WHY
        ↓
WE CHOSE WHAT TO DO
        ↓
WE CHECKED WHETHER MONEY WAS ALLOWED
        ↓
WE EXECUTED OR ESCALATED
        ↓
WE PROVED WHAT HAPPENED
        ↓
WE CAN EXPLAIN THE BUSINESS IMPACT
```

The final product should be judged from the implementation, not from inflated claims.

**Priority order:**

> **Correctness → Evidence → Reliability → Clarity → Visual polish → Documentation**

Do not reverse this order.