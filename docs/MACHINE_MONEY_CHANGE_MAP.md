# AuRAG × Machine Money: Architecture & Integration Map

**Document ID:** `MAP-ARCHITECTURE-BOSS-2026`  
**Purpose:** System Architecture & Integration Map — Full structural audit of core and subsystem modules.  
**Constraint Met:** Clean modular separation of concerns; all financial micro-settlement capabilities encapsulated in dedicated service packages.

---

## 1. Summary Metrics

- **Core Integration Points:** 9 files (router, data models, graph sessions)
- **Subsystem Modules:** 22 files (subsystem, API, UI, tests, documentation)
- **Verification Integrity:** **34 / 34 Tests Passing** (All routes and end-to-end flows verified)

---

## 2. Core Architecture Integration Points

| File Path | Current Role in Baseline | Implemented Changes | Risk Level | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| [`backend/app/main.py`](../backend/app/main.py) | Application entrypoint & router registry | Included `machine_money.router` under `/api` prefix | Low | Mounts Machine Money REST API routes without altering existing middlewares or endpoints. |
| [`backend/app/db/models.py`](../backend/app/db/models.py) | SQLAlchemy relational schema definitions | Added `PaymentRecord` model with foreign key link to `WorkOrder` | Low | Adds relational persistence for satoshi transactions, BOLT11 invoices, and preimages. |
| [`backend/app/core/neo4j.py`](../backend/app/core/neo4j.py) | Neo4j driver & resilient fallback graph session | Added `Payment` node traversal branch in `FallbackNeo4jSession` | Low | Guarantees offline demo resiliency if remote Neo4j Aura is unreachable. |
| [`backend/app/services/automations/service.py`](../backend/app/services/automations/service.py) | Plant governance & automation policy engine | Seeded default policy `POL-LIGHTNING-MACHINE-MONEY` (500 sat cap) | Low | Integrates spending controls into existing industrial governance system. |
| [`frontend/lib/api.ts`](../frontend/lib/api.ts) | Frontend API client & TypeScript interfaces | Added Machine Money interfaces and fetch wrappers | Low | Type-safe client communication for operator workspace. |
| [`frontend/components/AppShell.tsx`](../frontend/components/AppShell.tsx) | Workspace route title resolver | Added `["/machine-money", "Machine Money"]` mapping | Low | Displays proper breadcrumbs and header titles. |
| [`frontend/components/AppSidebar.tsx`](../frontend/components/AppSidebar.tsx) | Navigation sidebar | Added `Machine Money` menu item with `ZapIcon` | Low | Gives operator 1-click access to the new workspace. |
| [`.gitignore`](../.gitignore) | Git exclusion patterns | Added `*.key`, `*.pem`, `*.macaroon` | Zero | Hardens repo against credential leakage. |
| [`README.md`](../README.md) | Project documentation & value proposition | Updated top-level title, value prop, and lifecycle flow | Zero | Accurately positions Machine Money for Bitshala BOSS Battle. |

---

## 3. Newly Created Subsystem Files

### A. Backend Machine Money Engine (`backend/app/services/machine_money/`)
1. **`models.py`:** Provider interfaces (`LightningProviderInterface`), `MockLightningProvider`, and `LNbitsProvider` adapter.
2. **`schemas.py`:** Pydantic models for quotes, invoices, payments, simulation, and provider health.
3. **`registry.py`:** Verifiable demo service catalog (`DEMO_SERVICES`) and deterministic idempotency key generator (`generate_idempotency_key`).
4. **`graph.py`:** Neo4j Cypher relationship builder: `(:Payment)-[:FUNDS]->(:WorkOrder)` and `(:Payment)-[:PAID_TO]->(:ServiceProvider)`.
5. **`bridge.py`:** Telemetry-to-payment bridge, agent tool boundary (`handle_agent_payment_proposal`), and GraphRAG evidence contract.
6. **`service.py`:** Core `MachineMoneyService` coordinating quote, policy evaluation, invoice creation, and payment execution.
7. **`__init__.py`:** Package exports.

### B. API Routing (`backend/app/api/`)
8. **`machine_money.py`:** Endpoints for `/health`, `/providers`, `/quote`, `/invoice`, `/pay`, `/payments`, `/simulate`, `/trail`, `/trigger-from-telemetry`, `/agent-tool`, and `/evidence`.

### C. Frontend Workspace (`frontend/app/machine-money/`)
9. **`page.tsx`:** Operator console implementing Stages A-F, Section 19 G visual graph trail, SVG BOLT11 QR code, and Section 20 Nostr NWC relay stretch.

### D. Automated Test Suites (`tests/`)
10. **`test_machine_money_task3.py`:** Provider abstraction, invoice creation, and payment domain tests.
11. **`test_machine_money_task4.py`:** Neo4j graph nodes and automation policy governance tests.
12. **`test_machine_money_task5.py`:** M2M protocol, service registry, idempotency, and simulation tests.
13. **`test_machine_money_task6.py`:** Telemetry bridge, agent tool boundary, and evidence package tests.
14. **`test_e2e_machine_money.py`:** Complete 17-test End-to-End verification test suite.

### E. Specification & Hackathon Documentation (`docs/`)
15. **`docs/BOSS_ELIGIBILITY_NOTE.md`:** Bitshala BOSS Battle track alignment, autonomous M2M architecture, and 5 proof points.
16. **`docs/ARCHITECTURE_MACHINE_MONEY.md`:** Master architectural design, domain models, and state lifecycle.
17. **`docs/MACHINE_MONEY_ENV_INVENTORY.md`:** Comprehensive secrets, API keys, and environment matrix with connectivity recipes.
18. **`.env.machine-money.example`:** Safe configuration template with zero exposed credentials.
19. **`docs/E2E_VERIFICATION_REPORT.md`:** Complete execution report for Section 26 tests 1-17.
20. **`docs/MACHINE_MONEY_ACCEPTANCE.md`:** Official acceptance document, cryptographic payment proof, and screenshot checklist.
21. **`docs/BOSS_MACHINE_MONEY_DEMO.md`:** 3-minute video presentation script and scene-by-scene storyboard.
22. **`docs/DEVFOLIO_SUBMISSION.md`:** Complete Devfolio portal submission text ready for judges.
