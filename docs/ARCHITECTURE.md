# AuRAG Enterprise Architecture Specification

## 1. Executive Architecture Summary

**AuRAG** is an enterprise-grade, single-plant industrial operations and intelligence platform designed for high-hazard process manufacturing facilities (refineries, petrochemical complexes, and power plants). It unifies heterogeneous plant data silos—SAP Plant Maintenance (PM), OSIsoft PI Historian time-series streams, Microsoft 365 SharePoint engineering SOPs, and Quality Management Systems (QMS)—into a grounded, deterministic multi-agent GraphRAG reasoning engine.

The production deployment boundary is hosted in **AWS Mumbai (`ap-south-1`)** to comply with Indian data residency mandates, process safety guidelines (OSHA 1910.119 / OISD-156), and statutory regulations (The Factories Act 1948, PESO SMPV Rules).

---

## 2. Cloud Infrastructure & Network Topology (AWS Mumbai `ap-south-1`)

```
+----------------------------------------------------------------------------------------------------+
| AWS Region: ap-south-1 (Mumbai) - Multi-AZ VPC (10.20.0.0/16)                                      |
|                                                                                                    |
|   +---------------------------------------+  +---------------------------------------+             |
|   | Availability Zone A (ap-south-1a)     |  | Availability Zone B (ap-south-1b)     |             |
|   |                                       |  |                                       |             |
|   |   [Public Subnet 1]                   |  |   [Public Subnet 2]                   |             |
|   |   - NAT Gateway (Elastic IP)          |  |   - Standby Public Egress             |             |
|   |   - Application Load Balancer (ALB)   |  |   - Application Load Balancer (ALB)   |             |
|   |     (TLS 1.3 / Port 443)              |  |     (TLS 1.3 / Port 443)              |             |
|   +---------------------------------------+  +---------------------------------------+             |
|                       |                                          |                                 |
|                       +--------------------+---------------------+                                 |
|                                            |                                                       |
|   +----------------------------------------------------------------------------------+             |
|   | Private Application Subnets (ECS Fargate Cluster)                                |             |
|   |   [Task 1: FastAPI Backend API]           [Task 2: Next.js Frontend Console]     |             |
|   |   - Workers: 4 Uvicorn processes          - Static/SSR Standalone Runner         |             |
|   |   - Role: ecs-task-role (Least-Privilege) - Security: Non-root user (UID 1001)   |             |
|   |   - Security Headers (HSTS, CSP, XFO)     - Local Origin API Routing             |             |
|   +----------------------------------------------------------------------------------+             |
|                       |                                          |                                 |
|                       v                                          v                                 |
|   +---------------------------------------+  +---------------------------------------+             |
|   | Isolated Database Subnets             |  | AWS Managed Services                  |             |
|   |   - AWS RDS PostgreSQL Multi-AZ       |  |   - Amazon Bedrock                    |             |
|   |     (audit_events, approval_records)  |  |     (Claude 3.5 Sonnet / Haiku)       |             |
|   |   - Amazon ElastiCache Redis          |  |   - Amazon S3 Document Bucket         |             |
|   |     (JWKS cache, rate limits)         |  |     (SSE-KMS, Versioning enabled)     |             |
|   |   - Ingress: Port 5432 / 6379 from    |  |   - CloudWatch Logs & Metrics         |             |
|   |     ECS tasks only                    |  |     (30-day retention)                |             |
|   +---------------------------------------+  +---------------------------------------+             |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Core Subsystems

### 3.1 Enterprise Identity & Multi-Tenant Access Control
* **Identity Provider**: Microsoft Entra ID (Azure AD) via OpenID Connect (OIDC).
* **Token Verification**: Asymmetric RS256 signature verification against rotating JSON Web Key Sets (JWKS) with Redis caching.
* **4-Tier Industrial Clearance Hierarchy**:
  1. `OPERATIONAL`: Routine equipment status and search.
  2. `RESTRICTED`: SOPs and maintenance histories.
  3. `CONFIDENTIAL`: Incident RCAs and management logs.
  4. `REGULATORY_SENSITIVE`: DISH/PESO statutory audit records.
* **7 Role-Based Access Control (RBAC) Roles**: `PlantOperator`, `ReliabilityEngineer`, `SafetyInspector`, `MaintenancePlanner`, `OperationsLead`, `AutomationAdmin`, `PlantManager`.

### 3.2 Enterprise Data Connectors & Normalization Engine
* **SAP PM / EAM Connector**: Ingests functional locations (`FLOC`), equipment masters, and maintenance orders (`PM01`, `PM02`) with delta cursors.
* **OSIsoft PI Historian Connector**: Ingests sensor time-series telemetry (vibration, bearing temperature, discharge pressure) and computes rolling statistics (mean, peak, std_dev).
* **SharePoint Connector**: Synchronizes engineering drawings and SOPs with document version supersession (`Rev 1` -> `Rev 2`).
* **ANSI/ISA-5.1 Tag Normalizer**: Deterministically parses legacy tag variations (`P101`, `101-PUMP`, `P_101_A`) into canonical standards (`P-101`).
* **Quarantine Integrity Scanner**: Blocks corrupted or unverified files pending human review.

### 3.3 Grounded Multi-Agent GraphRAG Architecture
* **Hybrid Retrieval**: Combines Neo4j knowledge graph entity traversal, Qdrant dense embeddings, and BM25 sparse retrieval behind a cross-encoder reranker.
* **Multi-Agent Orchestration**: LangGraph supervisor coordinates 4 domain specialists:
  1. *Root Cause Analysis (RCA)*: Evaluates equipment failure sequences against P&IDs.
  2. *Statutory Compliance*: Audits against Factories Act 1948, OISD, and PESO rulebooks.
  3. *Predictive Maintenance*: Evaluates composite sensor health and turnaround windows.
  4. *Lessons Learned*: Queries historical work-order records for cross-failure patterns.
* **Claim-Level Grounding & Hallucination Mitigation**: Splits responses into discrete assertions, maps them to 200-character evidence snippets with page-level anchor links, and issues an explicit `INSUFFICIENT_EVIDENCE` fallback when evidence is lacking.

### 3.4 Enterprise Automation & Governance Engine
* **Configurable Policies**: Evaluates telemetry and compliance triggers against site-scoped policies with approval thresholds (`AUTONOMOUS` vs. `REQUIRES_APPROVAL`).
* **Safe Dry-Run Mode**: Simulates action execution without mutating databases or dispatching external calls.
* **Rollback Guidance**: Compiles step-by-step compensation procedures for every triggered action.
* **Immutable Audit Ledger**: Logs every query, citation, approval, and automation action in PostgreSQL, meeting OSHA 1910.119 and ISO 45001 standards.
