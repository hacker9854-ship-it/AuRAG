# PRD 4 — AuRAG Final Fixes, Verification & Submission Freeze

**Project:** AuRAG  
**Track:** Machine Money  
**Objective:** Close every remaining technical/documentation credibility gap identified in the latest audit, then freeze the repository for submission.

> Execute phases strictly in order. After each phase, run its tests and create the listed commit. Do not move forward if the acceptance gate fails.

---

# Phase 0 — Baseline & Final Audit

## Goal
Create a fresh baseline against the current repository head.

## Tasks

### 0.1 Record current repository state
Capture:
- branch
- HEAD SHA
- working-tree state
- deployment URLs
- current provider mode
- current test counts

### 0.2 Run complete validation

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

Browser E2E:
```powershell
npm run test:e2e
```

RAGAS:
```powershell
cd ..
python -m evaluation.validate_ragas
```

### 0.3 Create authoritative final snapshot
Create/update:

```text
docs/CURRENT_TEST_SNAPSHOT.md
```

The document must reference the exact final verification commit and the exact output of every command.

## Acceptance Gate
- All validation commands either pass or have documented non-blocking environment limitations.
- No stale test counts are carried forward.

## Commit
```text
chore(submission): refresh final verification baseline
```

---

# Phase 1 — Eliminate the Remaining Lightning Payment Loophole

## Goal
Ensure the mock Lightning provider can never create or report a cryptographic payment proof for an invalid or unregistered invoice.

## Problem to eliminate

Current risk:
- malformed invoice may be accepted
- unknown invoice may trigger fallback/random preimage generation
- returned preimage may not correspond to the invoice payment hash

## Tasks

### 1.1 Strict BOLT11 decode gate

In:

```text
backend/app/services/machine_money/providers/mock.py
```

`pay_invoice()` must first:
1. decode the invoice
2. validate BOLT11 structure
3. validate checksum/signature
4. extract payment hash
5. extract amount
6. validate expiry

Any failure must raise `ProviderError`.

### 1.2 Remove random preimage fallback

Delete every path that does:

```python
preimage = secrets.token_hex(...)
```

for an invoice that is not already registered.

Unknown invoice:

```text
decode
→ valid structure
→ payment hash not registered
→ REJECT
→ 0 sats deducted
```

### 1.3 Enforce the cryptographic invariant

Before simulated settlement:

```text
SHA256(preimage) == invoice.payment_hash
```

must be true.

If false:

```text
ProviderError
0 sats deducted
no MOCK_PAID state
```

### 1.4 Restrict mock provider registry

Only invoices created by the mock provider or explicitly registered test invoices may be settled.

No arbitrary invoice may be paid by the mock provider.

### 1.5 Payment-state integrity

A payment may reach:

```text
MOCK_PAID
```

only after:
- invoice valid
- registered
- hash matched
- preimage verified
- balance sufficient

## Required tests

Add/update:

```text
tests/test_bolt11.py
tests/test_machine_money_provider_failure.py
tests/test_e2e_machine_money.py
```

Test cases:
- malformed invoice rejected
- corrupt checksum rejected
- valid unregistered invoice rejected
- registered invoice succeeds
- mismatched preimage rejected
- expired invoice rejected
- zero sats lost on every rejection

## Acceptance Gate

All of the following must hold:

```text
invalid invoice      → reject
unknown invoice      → reject
wrong preimage       → reject
valid registered     → success
sha256(preimage)     → payment_hash
```

## Commit

```text
fix(machine-money): close invalid-invoice and preimage-proof loopholes
```

---

# Phase 2 — Finalize Vendor Federation Honesty & Binding

## Goal
Keep the multi-vendor RFQ feature technically useful without overstating it as a real external marketplace.

## Current architecture

The project contains:

```text
/api/vendors/*
```

but the vendor registry is still local and preconfigured.

Therefore the current feature must be described as:

> **HTTP-based federation interface with 3 pre-approved synthetic vendor nodes**

unless genuinely external services are deployed.

## Tasks

### 2.1 Normalize vendor disclosure

Use exactly three canonical nodes:

```text
Apex Diagnostics
Precision Dynamics
Quantum Reliability
```

UI label:

```text
3 PRE-APPROVED SYNTHETIC VENDOR NODES
```

### 2.2 Normalize implementation wording

Do not say:

```text
Real vendor marketplace
Live external contractors
Live vendor APIs
```

unless that is literally true.

Use:

```text
HTTP vendor-node federation interface
Synthetic/pre-approved vendor nodes
Dynamic quote generation
```

### 2.3 Bind RFQ to payment

The final payment must reference:

```text
rfq_id
candidate_id
vendor_id
quote_id
service_id
work_order_id
amount_sats
payment_id
```

A payment without a valid selected quote must fail.

### 2.4 Add RFQ integrity test

Test:

```text
selected vendor
→ selected quote
→ generated invoice
→ payment
```

and ensure the final proof drawer shows the same vendor and amount.

### Acceptance Gate

No README/UI/document says the synthetic nodes are independent real vendors.

Payment proof demonstrates RFQ-to-payment binding.

## Commit

```text
fix(machine-money): finalize vendor federation disclosure and binding
```

---

# Phase 2A — Public Industrial Data + Independent Vendor Webhooks

## Objective
Increase the credibility of the Machine Money pipeline WITHOUT pretending synthetic data is real.

The final architecture supports:
Public/Replayable Industrial Dataset
        ↓
Telemetry Normalization
        ↓
Anomaly Detection
        ↓
Grounded GraphRAG
        ↓
Vendor HTTP RFQ Federation
        ↓
Policy Gate
        ↓
Lightning Payment
        ↓
Proof / Audit

## Tasks

### 2A.1 Audit current telemetry pipeline
Identify and audit current source, synthetic/generated fields, replayable fields, transformation path, and destination event schema.
Document in `docs/TELEMETRY_PROVENANCE_AUDIT.md`.

### 2A.2 Add a public dataset replay adapter
Add dataset adapter abstraction under `telemetry/adapters/` (`base.py`, `public_dataset.py`, `synthetic.py`, `opcua.py`).
Normalize input into telemetry event schema with provenance metadata (`data_source_type`, `dataset_name`, `dataset_record_id`, `source_reference`, `replay_mode`).
UI labels must distinguish `PUBLIC DATASET / REPLAY`, `SYNTHETIC DEMO`, and `LIVE SCADA`.

### 2A.3 Choose a suitable public dataset
Integrate NASA IMS Bearing Run-to-Failure dataset (Test 2, Bearing 1 outer race failure) with a small representative progression fixture (`telemetry/fixtures/nasa_ims_bearing_sample.json`).
Document in `docs/PUBLIC_DATASET_PROVENANCE.md`.

### 2A.4 Map public data to the canonical demo
Maintain canonical synthetic demo (`P-101A`) while routing public replay through `REPLAY-ASSET-01`.

### 2A.5 Public-dataset evidence through GraphRAG
Retrieved evidence for replayed events must expose provenance (`source_type: PUBLIC_DATASET`, `dataset`, `record_id`, `score`). Fallback labeled `CONTROLLED DEMO FIXTURE`.

### 2A.6 Create independent mock vendor webhook services
Independently addressable vendor microservices under `services/vendor_apex/`, `services/vendor_precision/`, and `services/vendor_quantum/` exposing `POST /quote` and `GET /health` with HTTP-federated vendor quotes, SLA, and BOLT11 invoices.

### 2A.7 Real HTTP RFQ dispatch
RFQ engine discovers configured vendor nodes via environment URLs (`VENDOR_APEX_URL`, etc.), dispatches real HTTP POST `/quote`, validates response schema, handles timeouts/HTTP 500s, runs scoring, and binds vendor node → rfq_id → quote_id → invoice → payment_id.

### 2A.8 Vendor disclosure
Vendor UI cards state `DEMO VENDOR NODE` or `PRE-APPROVED DEMO VENDOR`. No false claims of live external marketplaces.

### 2A.9 Optional OPC-UA adapter
Inspect and implement testbed adapter `telemetry/adapters/opcua.py` with explicit disclosure.

### 2A.10 UI data provenance
Visible source badges on telemetry and evidence views (`[SYNTHETIC DEMO]`, `[PUBLIC DATASET / REPLAY]`, `[LIVE SCADA]`).

### 2A.11 Automated tests
Add unit and integration tests:
- `tests/test_public_dataset_adapter.py`
- `tests/test_vendor_webhooks.py`
- `tests/test_e2e_public_data_machine_money.py`

### 2A.12 Documentation
Create/update:
- `docs/PUBLIC_DATASET_PROVENANCE.md`
- `docs/VENDOR_FEDERATION.md`
- `docs/TELEMETRY_PROVENANCE_AUDIT.md`
- `README.md` Data Provenance section

### 2A.13 Judge Mode preset
Add `PUBLIC DATASET REPLAY` preset to Judge Mode without replacing canonical happy path.

### 2A.14 RAGAS regression
Run `python -m evaluation.validate_ragas` to verify GraphRAG quality with fresh commit.

### 2A.15 Security
Verify environment configuration, run `python scripts/secret_scan.py` to ensure no credentials or private keys are exposed.

## Acceptance Gate
- Public dataset adapter exists and provenance documented.
- Public replay mode works without breaking synthetic mode.
- UI clearly differentiates source types (`[PUBLIC DATASET / REPLAY]` vs `[SYNTHETIC DEMO]`).
- Three vendors are independently HTTP-addressable demo services.
- Real HTTP RFQ dispatch with error handling and quote-to-payment binding.
- Secret scan passes.
- RAGAS validation passes.
- Full test suite passes.

## Commit
```text
feat(data): add public industrial replay and vendor federation
```

---

# Phase 3 — Graph / AuraDB Resilience Verification

## Goal
Make the graph view work even when AuraDB/remote Neo4j is paused or unavailable, without showing false live connectivity.

## Tasks

### 3.1 Verify remote Neo4j path

Check:
- URI
- credentials availability
- database selection
- connection timeout
- graph API response

### 3.2 Keep resilient fallback

Current fallback must support:
- equipment traversal
- failure events
- work orders
- procedures
- regulatory clauses
- payment lineage
- graph path rendering

### 3.3 Truthful readiness state

When remote Neo4j is unavailable:

```text
GRAPH STATUS
DEGRADED / FALLBACK
```

Never:

```text
ALL SYSTEMS NOMINAL
```

unless actual service health supports that claim.

### 3.4 Graph panel behavior

Verify:
- no React key duplication
- no blank panel
- no fatal error
- no fake connected status
- fallback graph visibly identified

### 3.5 Add graph health tests

Test:
- live connection success
- remote connection failure
- fallback traversal success
- payment graph trail fallback
- graph API deduplication

## Acceptance Gate

Judge opening the graph panel during a remote Neo4j outage must still see a functioning, clearly labeled fallback view.

## Commit

```text
fix(graph): finalize truthful Neo4j fallback and health diagnostics
```

---

# Phase 4 — Final RAGAS Quality Gate

## Goal
Ensure the retrieval layer is backed by a reproducible quality measurement, not only unit tests.

## Tasks

### 4.1 Run authoritative RAGAS acceptance

Command:

```powershell
python -m evaluation.validate_ragas
```

### 4.2 Verify ground-truth coverage

Every case in:

```text
agents/ground_truth.json
```

must:
- execute
- receive a scored result
- meet the configured threshold

### 4.3 Record exact metrics

Create/update:

```text
docs/RAGAS_FINAL_VERIFICATION.md
```

Include:
- evaluation date/time
- final commit SHA
- number of cases
- configured threshold
- Faithfulness
- Context Precision
- Context Recall if enabled
- Answer Relevancy
- case-level failures, if any

### 4.4 Release gate

If any scored metric falls below the configured threshold:

```text
FAIL RELEASE
```

If provider infrastructure is unavailable:

```text
FAIL RELEASE
```

Do not silently substitute fixture scores.

### 4.5 Judge-facing wording

README may say:

> `RAGAS acceptance gate verified on the final commit`

only when the fresh run passes.

## Acceptance Gate

All selected cases:
- scored
- no skipped cases
- no provider errors
- every required metric passes threshold

## Commit

```text
test(ragas): verify final retrieval quality acceptance gate
```

---

# Phase 5 — Remove Remaining README Overclaims

## Goal
Make every major claim exactly match implementation.

## 5.1 Replace these phrases

### Remove
```text
industrial-grade implementation
first industrial-grade
unforgeable audit evidence
real vendor APIs
loss prevented
guaranteed ROI
sub-second Lightning finality
```

### Prefer
```text
industrial Machine Money workflow
cryptographically verifiable payment-state evidence
3 pre-approved synthetic vendor nodes
modelled downtime exposure
measured demo execution time
provider-reported live settlement
```

## 5.2 Separate demo from production

Create a clear section:

```text
## What Is Live Today
```

Example structure:

| Capability | Public Demo |
|---|---|
| Frontend | Live |
| Backend | Live |
| Judge Mode | Live |
| Lightning | Mock / Simulation unless live provider configured |
| BOLT11 | Standards-valid test invoices |
| Vendors | 3 synthetic/pre-approved nodes |
| Graph | Neo4j when available, resilient fallback otherwise |
| Economics | Synthetic/modelled scenario |
| RAGAS | Final acceptance-gated retrieval |

### 5.3 Proof wording

Mock mode:

> `Simulation integrity verified: SHA-256(preimage) == payment_hash`

Live mode:

> `Provider-reported Lightning settlement evidence`

Never merge these meanings.

### 5.4 Performance wording

Use:

> `Measured demo execution time`

Do not imply that the number is a global Bitcoin network settlement guarantee.

### Acceptance Gate

Search the entire README for:

```text
first
industrial-grade
production-grade
unforgeable
real vendor
vendor APIs
loss prevented
guaranteed
sub-second finality
```

Every occurrence must be reviewed.

## Commit

```text
docs(readme): finalize claim accuracy and demo-versus-production wording
```

---

# Phase 6 — Canonical Numbers & Documentation Consistency

## Goal
Eliminate all contradictions.

## Canonical values

```text
Autonomous payment:
250 sats

Autonomous cap:
500 sats

Escalation:
1,200 sats

Vendors:
3

Modelled downtime:
4.5h

Modelled exposure:
$1.17M

Modelled exposure-to-cost multiple:
7,800,000:1
```

## Tasks

Search repository for stale values:

```text
50 sats
250 sats
500 sats
750 sats
1200 sats
3 vendors
4 vendors
7.2M
7.8M
136
141
```

Exceptions are allowed only in historical documentation or explicit test scenarios.

### 6.1 Test-count synchronization

Current authoritative final test count must come from the latest actual run.

Do not maintain:
- old badge
- old README number
- old verification report

alongside the final number.

### 6.2 Snapshot commit synchronization

`docs/CURRENT_TEST_SNAPSHOT.md` must reference the final verified commit SHA.

## Acceptance Gate

No unexplained stale value remains in primary submission docs.

## Commit

```text
docs(submission): synchronize canonical values and verification snapshot
```

---

# Phase 7 — Final Judge Screenshots

## Goal
Every README screenshot must show a meaningful state in the current UI.

## Required screenshots

```text
1. machine-money-above-fold.png
2. machine-money-execution-timeline.png
3. machine-money-rfq.png
4. machine-money-policy-escalation.png
5. machine-money-proof-drawer.png
6. machine-money-provider-failure.png
7. machine-money-economics.png
```

## Required visible states

### Screenshot 1
- Judge Mode
- 250 sats
- provider mode
- 500-sat cap
- business impact

### Screenshot 2
- populated execution timeline

### Screenshot 3
- all three vendors
- selection strategy
- selected vendor

### Screenshot 4
- 1,200 sats
- PENDING_APPROVAL
- human approval path

### Screenshot 5
- BOLT11
- payment hash
- preimage verification
- graph lineage
- provider mode

### Screenshot 6
- provider failure
- zero funds lost
- remediation guidance

### Screenshot 7
- modelled exposure
- assumptions
- formula
- sensitivity

## Acceptance Gate

No screenshot caption claims a state that is not actually visible in the image.

## Commit

```text
docs(machine-money): refresh final judge-state screenshots
```

---

# Phase 8 — Final Test & Browser Rehearsal

## Goal
Run the complete product exactly as a judge will see it.

## Browser flow

```text
1. Open /machine-money
2. Verify initial state
3. Click RUN INDUSTRIAL EMERGENCY
4. Verify timeline
5. Verify RFQ
6. Verify policy
7. Verify payment
8. Open proof drawer
9. Verify causal evidence
10. Reset
11. Run 1,200-sat escalation
12. Approve
13. Verify settlement
14. Reset
15. Run provider failure
16. Verify FAILED
17. Verify 0 sats lost
```

## Check

- console errors
- network errors
- hydration errors
- broken images
- broken buttons
- stale state
- modal trapping
- mobile responsive behavior

## Acceptance Gate

Three complete judge scenarios work in a fresh browser session.

## Commit

```text
test(submission): complete final browser rehearsal and regression pass
```

---

# Phase 9 — Final Release Package

## Tasks

### 9.1 Run final command set

```powershell
.\.venv\Scripts\pytest.exe -q
cd frontend
npm test -- --run
npm run lint
npm run build
npm run test:e2e
cd ..
python -m evaluation.validate_ragas
```

### 9.2 Secret scan

```powershell
.\.venv\Scripts\python.exe scripts/secret_scan.py
```

### 9.3 Link audit

Run repository documentation link audit.

### 9.4 Working tree

```powershell
git status
git diff --check
```

Working tree must be clean.

### 9.5 Final README verification

Verify:
- live demo URL
- repository URL
- screenshots
- test snapshot
- RAGAS report
- Machine Money verification
- eligibility/provenance docs
- demo script

## Acceptance Gate

Every release gate passes.

## Commit

```text
chore(release): freeze AuRAG for hackathon submission
```

---

# Phase 10 — Final Submission Freeze

## Do not change architecture after this phase.

Only emergency fixes are allowed.

## Freeze rules

Do not:
- add unrelated features
- add another database
- change provider architecture
- add another LLM only for presentation
- rewrite Git history
- backdate commits
- fabricate test results
- fabricate live vendor activity
- fabricate Lightning settlement

## Final artifact set

Must contain:

```text
README.md
docs/CURRENT_TEST_SNAPSHOT.md
docs/RAGAS_FINAL_VERIFICATION.md
docs/CLAIM_EVIDENCE_MATRIX.md
docs/MACHINE_MONEY_VERIFICATION.md
docs/JUDGE_DEMO_SCRIPT.md
docs/HACKATHON_ELIGIBILITY.md
final screenshots
```

## Final release command

```powershell
git status
git log -10 --oneline
git diff --check
```

Then push only the genuine final state.

## Final Commit

```text
chore(release): freeze AuRAG final hackathon submission
```

---

# Final Definition of Done

AuRAG is considered complete only when:

```text
[PASS] Invalid invoice rejected
[PASS] Unknown invoice rejected
[PASS] Preimage hash invariant enforced
[PASS] Valid BOLT11 invoice generated
[PASS] QR round-trip verified
[PASS] RFQ uses 3 disclosed synthetic nodes
[PASS] RFQ is bound to payment
[PASS] Neo4j failure does not break graph UX
[PASS] Fallback graph is clearly labeled
[PASS] Fresh RAGAS acceptance passes
[PASS] README contains no unsupported superlatives
[PASS] Demo/live boundaries are explicit
[PASS] Canonical numbers are consistent
[PASS] Test snapshot references final commit
[PASS] Screenshots match current UI
[PASS] Full backend tests pass
[PASS] Full frontend tests pass
[PASS] Browser E2E passes
[PASS] Production build passes
[PASS] Secret scan passes
[PASS] Documentation links pass
[PASS] Working tree clean
[PASS] Final demo rehearsed
```

# Release Priority

```text
1. Payment correctness
2. Graph reliability
3. RAGAS verification
4. RFQ/payment integrity
5. README truthfulness
6. Documentation consistency
7. Screenshots
8. Final rehearsal
9. Freeze
```

**Do not optimize for feature count now. Optimize for a judge being unable to find a contradiction between the UI, code, tests, and README.**