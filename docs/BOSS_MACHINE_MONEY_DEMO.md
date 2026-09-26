# AuRAG × Machine Money: 3-Minute Video Demo Script & Storyboard

**Video Target Duration:** 3 minutes 45 seconds  
**Track:** Machine Money Track ($1,000 Prize) — Bitshala BOSS Battle 2026 (Devfolio)  
**Presenter:** Niss (@hacker9854-ship-it) <nishant.ai.eng@gmail.com>  
**Live Demo Route:** [`http://localhost:3000/machine-money`](http://localhost:3000/machine-money)

---

## Storyboard & Timing Overview

```text
0:00 - 0:20 │ THE PROBLEM: AI Can Detect, But Cannot Settle
0:20 - 0:50 │ THE TRIGGER: P-101A Predictive Vibration Excursion
0:50 - 1:20 │ THE EVIDENCE: GraphRAG Traversal (FE-001, WO-1002, PROC-001)
1:20 - 1:45 │ THE SERVICE QUOTE: 250 sats on maintenance-node-a
1:45 - 2:05 │ THE POLICY ENGINE: 250 sats ≤ 500 sat Cap (Allowed)
2:05 - 2:25 │ THE SETTLEMENT: Lightning BOLT11 Invoice & Preimage Proof
2:25 - 2:45 │ THE RECEIPT: Status PAID, Hash & Zero-Routing Fee
2:45 - 3:10 │ THE GRAPH TRAIL: Causal Chain in Neo4j Ontology
3:10 - 3:30 │ GROUNDED REASONING: "Why Did the Machine Spend Money?"
3:30 - 3:45 │ THE AUDIT: Dual-Layer Persistence & Closing Impact
```

---

## Detailed Scene-by-Scene Script

### Scene 1: The Core Problem (0:00 – 0:20)
- **On Screen:** Title Slide / AuRAG Command Center Header.
- **Visual Focus:** Split screen showing an industrial refinery pump on the left and a banking approval hurdle on the right.
- **Speaker Narration:**
  > *"Welcome to AuRAG. Today, industrial AI systems can detect complex equipment failures hours before disaster strikes. But acting on that insight still grinds to a halt because payments rely on human credit cards, purchase orders, and bureaucracy. When a critical slurry pump is failing, waiting 48 hours for human invoicing causes catastrophic plant downtime.*  
  > *What if the machine could reason over its own operational evidence and settle its own maintenance over the Bitcoin Lightning Network? Let’s see it live."*

---

### Scene 2: The Predictive Excursion Trigger (0:20 – 0:50)
- **On Screen:** Navigate to [`/machine-money`](http://localhost:3000/machine-money).
- **Operator Action:** Click **"Scenario 1: Autonomous Telemetry Settle"** button or view Stage A.
- **Visual Focus:** Stage A Card highlights: `P-101A (Slurry Feed Pump)`, `High Risk (94%)`, Vibration excursion spike to `5.8 mm/s` (threshold `2.5 mm/s`).
- **Speaker Narration:**
  > *"Here in the Machine Money operator workspace, our telemetry listener detects an anomalous vibration excursion on Centrifugal Slurry Pump P-101A. The signal has spiked to 5.8 millimeters per second—far above our safe threshold of 2.5. AuRAG's predictive model flags this with 94% confidence as an impending catastrophic bearing seizure."*

---

### Scene 3: GraphRAG Operational Evidence (0:50 – 1:20)
- **On Screen:** Stage B (Evidence Package Card) in the lifecycle pipeline.
- **Visual Focus:** Highlight `FE-001 (Bearing Degradation)`, `WO-1002 (Prior Excursion Overhaul)`, `PROC-001 (Laser Alignment Standard)`.
- **Speaker Narration:**
  > *"Unlike black-box models, AuRAG does not spend money blindly. It traverses our Neo4j operational knowledge graph. It matches the vibration signature against historical Failure Event FE-001, recalls prior Work Order WO-1002, and binds to Standard Operating Procedure PROC-001. This cross-layer evidence package proves exactly why immediate intervention is necessary before a single satoshi is spent."*

---

### Scene 4: Service Discovery & Machine-to-Machine Quote (1:20 – 1:45)
- **On Screen:** Stage C (Service Quote Card).
- **Visual Focus:** Highlight Service `Bearing Inspection & Laser Alignment`, Provider `maintenance-node-a`, Quoted Cost `250 sats` (0.00000250 BTC), SLA `2.0 hrs`.
- **Speaker Narration:**
  > *"AuRAG queries our verifiable service provider registry. Specialist node 'maintenance-node-a' issues a cryptographically verifiable quote: 250 satoshis for an ultrasonic bearing diagnostic and laser alignment, with an automated SLA of 2 hours and replacement parts included."*

---

### Scene 5: Zero-Trust Spending Policy Governance (1:45 – 2:05)
- **On Screen:** Stage D (Policy Engine Card).
- **Visual Focus:** Highlight `POL-LIGHTNING-MACHINE-MONEY`, Auto-pay cap `500 sats`, Result `Allowed (250 <= 500)`, Deterministic idempotency hash.
- **Speaker Narration:**
  > *"Before any wallet moves funds, the transaction must pass AuRAG’s strict zero-trust policy engine: Policy POL-LIGHTNING-MACHINE-MONEY. The autonomous cap is set to 500 sats. Because 250 sats is within the cap and the vendor is in our approved registry, autonomous execution is authorized. If the quote were 1,200 sats—like a major motor rewind—the system would automatically halt and escalate to a human lead engineer for digital sign-off."*

---

### Scene 6: Instant Lightning Network Settlement (2:05 – 2:25)
- **On Screen:** Stage E (Lightning Micro-Payment Card) & BOLT11 QR Code.
- **Visual Focus:** Live BOLT11 invoice string `lnbc2500n1...`, QR Code, and status transition from `Pending` $\rightarrow$ `Paid (Settled)`.
- **Speaker Narration:**
  > *"The service provider generates a standard BOLT11 Lightning invoice. AuRAG pays the invoice instantaneously over the Lightning Network. Within 15 milliseconds, the invoice is settled! We receive a cryptographic SHA-256 preimage proof confirming settlement with zero routing fees."*

---

### Scene 7: Operational Outcome & Work Order Dispatch (2:25 – 2:45)
- **On Screen:** Stage F (Operational Outcome Card).
- **Visual Focus:** Target Work Order `WO-2026-P101` changes status to `FUNDED / DISPATCHED`.
- **Speaker Narration:**
  > *"Look at Stage F: Work Order WO-2026-P101 is now officially funded and dispatched to the field contractor. The machine has resolved its own impending failure autonomously, averting an estimated 4.5 hours of unbudgeted plant downtime."*

---

### Scene 8: The Causal Graph Trail (2:45 – 3:10)
- **On Screen:** Section 19 G (Operational Graph Trail Card).
- **Visual Focus:** Follow the visual node sequence:  
  `Equipment (P-101A)` $\rightarrow$ `PredictiveEvent (EVT-VIB-001)` $\rightarrow$ `WorkOrder (WO-2026-P101)` $\leftarrow$ `Payment (PAY-...)` $\rightarrow$ `ServiceProvider (maintenance-node-a)`.
- **Speaker Narration:**
  > *"Every step is committed directly into our Neo4j knowledge graph. Here is the complete causal chain: Equipment P-101A suffered an excursion, triggering Predictive Event EVT-VIB-001, which generated Work Order WO-2026-P101, funded by Payment PAY-2026, paid to Service Provider maintenance-node-a. Any plant auditor can inspect the exact Cypher query and see the mathematical proof of every satoshi spent."*

---

### Scene 9: Grounded Copilot Explanation (3:10 – 3:30)
- **On Screen:** Copilot Chat / Evidence Drawer.
- **Operator Action:** Ask: *"Why did the machine spend money on P-101A?"*
- **Visual Focus:** Response appears with grounded citations to `FE-001`, `PROC-001`, and `POL-LIGHTNING-MACHINE-MONEY`.
- **Speaker Narration:**
  > *"When an executive or plant superintendent asks the AI: 'Why did the machine spend money?', AuRAG doesn’t hallucinate. It pulls the grounded evidence: 'Payment of 250 sats authorized to avert failure mode FE-001 under procedure PROC-001 per policy cap.' Full transparency from sensor to satoshi."*

---

### Scene 10: Dual-Layer Audit & Conclusion (3:30 – 3:45)
- **On Screen:** Settlement Ledger Table & Nostr Relay Card (Section 20).
- **Visual Focus:** Ledger row showing payment ID, timestamp, and NIP-47 / NIP-90 relay readiness status.
- **Speaker Narration:**
  > *"Every payment is dual-persisted across PostgreSQL and Neo4j with deterministic SHA-256 idempotency preventing any double-spend, and our Nostr NWC protocol adapter ensures forward compatibility with peer-to-peer data vending machines.*  
  > *AuRAG proves that Machine Money on Bitcoin Lightning is not a speculative gimmick—it is the future of autonomous, resilient industrial infrastructure. Thank you!"*

---

## Recording Tips for the Presenter

1. **Resolution:** 1080p (1920x1080) at 60 FPS.
2. **Audio:** Clear USB condenser microphone with zero background noise.
3. **Pacing:** Speak with confident, authoritative cadence. Do not rush through the graph trail.
4. **Browser Zoom:** Set browser zoom to 100% or 110% so all text, badges, and QR codes are crisp and legible.
5. **Demonstration Order:** Trigger Scenario 1 live on camera to showcase the real-time badge transition from `Pending` to `Paid (Settled)`.
