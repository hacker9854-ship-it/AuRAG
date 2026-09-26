# Architecture Specification: Machine Money × AuRAG Minimal-Change Design

**Document ID:** `DOC-ARCH-MACHINE-MONEY-01`  
**Phase:** Task 2 (Sections 4 – 6)  
**Status:** Approved for Implementation  
**Lead Architect:** AuRAG Engineering Team  

---

## 1. Executive Summary

This architecture specification formalizes the transformation of AuRAG from an advisory industrial intelligence platform into an autonomous, closed-loop agent that can detect equipment degradation, verify procedural evidence via GraphRAG, and settle service and parts transactions over Bitcoin's Lightning Network.

The guiding architectural principle is **Minimal-Change Non-Destructive Extension**:
- **Zero modification** to existing retrieval, ingestion, LangGraph supervisor, or sensor telemetry pipelines.
- The Machine Money capability is introduced as an additive, decoupled subsystem (`backend/app/domain/machine_money/` and `backend/app/api/machine_money.py`).

---

## 2. AuRAG Baseline Preservation Matrix

The following table itemizes the core AuRAG subsystems that are preserved in their entirety:

| Subsystem | Existing Path | Preserved Functionality | Modification Scope |
|---|---|---|---|
| **LangGraph Supervisor** | `agents/supervisor.py` | Multi-agent coordination, intent classification, and state transitions. | **Zero change** — payment tool will be injected via standard LangGraph tool registry. |
| **Copilot & RCA Agents** | `agents/copilot.py`, `agents/rca.py` | Root-cause analysis, equipment diagnostic reasoning, and citation synthesis. | **Zero change** — outputs consumed as evidence payload. |
| **Industrial Knowledge Graph** | `backend/app/core/neo4j.py`, `infra/neo4j/` | Nodes: `Equipment`, `FailureEvent`, `WorkOrder`, `Procedure`. | **Additive only** — new node `(:Payment)` and edges `[:FUNDS]`, `[:TRIGGERED_BY]`. |
| **Hybrid Retrieval** | `retrieval/hybrid.py`, `retrieval/qdrant_store.py` | Dense vector (Qdrant) + BM25 sparse search + Cohere/Local reranking. | **Zero change** — untouched. |
| **Telemetry Pipeline** | `telemetry/generator.py`, `telemetry/worker.py` | P-101 vibration & bearing temperature streaming, health index scoring. | **Zero change** — anomaly triggers read via message queue/events. |
| **Enterprise Governance** | `backend/app/db/models.py` | `ApprovalRecord`, `AutomationPolicy`, `AuditEvent`. | **Additive only** — payment actions map directly to policy thresholds. |
| **Existing REST APIs** | `backend/app/api/*.py` | Chat, telemetry, equipment, work orders, connectors, automations. | **Zero change** — all existing routes remain 100% backward compatible. |

---

## 3. The Gap: Pre-Hackathon vs. Machine Money

```
PRE-HACKATHON (Advisory Only):
[Sensor Telemetry] ──> [Anomaly Detect] ──> [GraphRAG Evidence] ──> [Draft Work Order] ──> [STOP (Human Manual Invoice)]

MACHINE MONEY (Closed-Loop Agency):
[Sensor Telemetry] ──> [Anomaly Detect] ──> [GraphRAG Evidence] ──> [Draft Work Order]
                                                                           │
                                                                           ▼
                                                                  [Provider Quote]
                                                                           │
                                                                           ▼
                                                              [Policy Limit Evaluation]
                                                               ├─ <= 500 sats ─> [AUTONOMOUS M2M SETTLEMENT]
                                                               └─ > 500 sats  ─> [Operator Approval Queue]
                                                                           │
                                                                           ▼
                                                                  [BOLT11 Invoice]
                                                                           │
                                                                           ▼
                                                              [Lightning Node Payment]
                                                                           │
                                                                           ▼
                                                        [Receipt Attached to WorkOrder & Neo4j]
```

---

## 4. Minimal-Change Directory Layout

New files are strictly isolated under `backend/app/domain/machine_money/` and an API controller:

```text
backend/app/
├── api/
│   ├── ... (existing routers)
│   └── machine_money.py           <-- NEW: REST API endpoints for quotes, payments, invoices
├── db/
│   ├── models.py                  <-- ADDITIVE: PaymentIntent, PaymentReceipt, ProviderQuote models
│   └── database.py                <-- Preserved (SQLite fallback active, PostgreSQL/Supabase ready)
├── domain/
│   └── machine_money/             <-- NEW: Isolated Machine Money Domain
│       ├── __init__.py
│       ├── models.py              <-- Pydantic domain schemas (PaymentIntent, BOLT11Invoice, Receipt)
│       ├── provider.py            <-- LightningProvider Protocol abstraction
│       ├── mock_provider.py       <-- Resilient offline test provider (100% deterministic)
│       ├── lnbits_provider.py     <-- Live LNbits Lightning node integration
│       └── service.py             <-- Policy verification, quotation, settlement orchestration
```

---

## 5. Subsystem Contracts & Interaction Flow

### 5.1 Payment Provider Protocol (`LightningProvider`)
```python
from typing import Protocol, Optional
from backend.app.domain.machine_money.models import (
    InvoiceRequest, BOLT11Invoice, PaymentReceipt, ProviderHealth
)

class LightningProvider(Protocol):
    async def health(self) -> ProviderHealth: ...
    async def create_invoice(self, req: InvoiceRequest) -> BOLT11Invoice: ...
    async def pay_invoice(self, bolt11: str, max_fee_sats: int = 10) -> PaymentReceipt: ...
    async def check_payment(self, payment_hash: str) -> PaymentReceipt: ...
```

### 5.2 Automation Policy Integration
Machine Money transactions are subject to existing `AutomationPolicy` rules:
- **Policy Check:** Look up active policy where `trigger_type == "EQUIPMENT_ANOMALY"` and `action_type == "EXECUTE_LIGHTNING_PAYMENT"`.
- **Tier 1 (Autonomous):** If quoted amount $\le$ `MACHINE_MONEY_MAX_AUTOPAY_SATS` (default 500 sats) and `MACHINE_MONEY_AUTO_PAY_ENABLED == True`:
  - Execute payment immediately via provider.
  - Status set to `SETTLED`.
  - Log audit event with status `AUTONOMOUS_PAYMENT_SUCCESS`.
- **Tier 2 (Human-in-the-Loop):** If quoted amount $>$ threshold or autopay disabled:
  - Create `ApprovalRecord` with status `PENDING`.
  - Hold invoice in `PENDING_OPERATOR_APPROVAL` state.
  - Notify operator in the UI console.

### 5.3 Knowledge Graph Persistence
Upon successful settlement:
```cypher
MATCH (wo:WorkOrder {id: $work_order_id})
MATCH (evt:PredictiveEvent {id: $event_id})
CREATE (p:Payment {
    id: $payment_id,
    payment_hash: $payment_hash,
    preimage: $preimage,
    amount_sats: $amount_sats,
    provider: $provider,
    settled_at: datetime($settled_at),
    status: "SETTLED"
})
CREATE (p)-[:FUNDS]->(wo)
CREATE (p)-[:TRIGGERED_BY]->(evt)
```

---

## 6. Verification & Non-Regression Guarantee

1. **Zero Route Collisions:** All Machine Money routes are namespaced under `/api/machine-money/*`.
2. **Offline Immunity:** If no Lightning node or network connection is available, `MACHINE_MONEY_PROVIDER=mock` executes full invoice generation and settlement verification without crashing or blocking.
3. **Database Portability:** Works seamlessly on local SQLite (`.runtime/aurag_enterprise.db`) and scales directly to Supabase/PostgreSQL with identical schema definitions.
