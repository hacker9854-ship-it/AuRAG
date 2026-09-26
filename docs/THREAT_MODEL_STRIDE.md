# AuRAG Enterprise STRIDE Threat Model & Security Review

This document establishes the threat model and defense-in-depth security architecture for **AuRAG**, following the Microsoft STRIDE methodology.

---

## 1. Threat Classification Matrix

| Category | Threat Description | Affected Component | Impact | Implemented Mitigation |
|---|---|---|---|---|
| **Spoofing** | Attacker presents forged JWT token to impersonate plant operator or engineer. | `backend/app/core/auth.py` | Critical | **Entra ID OIDC RS256 Verification**: Tokens verified cryptographically using public keys fetched dynamically from Microsoft JWKS endpoints with TTL-bounded caching. Symmetric HMAC tokens rejected. |
| **Spoofing** | Cross-tenant parameter manipulation to view other site's drawings. | `backend/app/core/tenant.py` | High | **SiteContext Scoping**: Site ID extracted from verified JWT claims (`site_id`) and injected into queries via FastAPI dependency injection. |
| **Tampering** | Operator or attacker alters past safety audit records or work order approval logs. | `backend/app/db/models.py` | Critical | **Immutable Audit Ledger**: Append-only `AuditEvent` and `ApprovalRecord` tables with auto-generated UUIDs, UTC timestamps, and no exposed update/delete APIs. |
| **Tampering** | Ingestion of malformed or corrupted P&ID drawings intended to degrade search index. | `ingestion/quarantine.py` | High | **Quarantine Integrity Scanner**: Mandatory SHA256 checksum, magic byte inspection (`%PDF-`), and quarantine isolation queue for unverified files. |
| **Repudiation** | Engineer denies approving an emergency pump overhaul or policy change. | `backend/app/services/audit.py` | High | **Cryptographic User Attribution**: Every approval action logs the approver's Entra user ID, role, client IP address, timestamp, and target payload into PostgreSQL. |
| **Information Disclosure** | Leakage of plant personnel Aadhaar numbers, phone numbers, or emails to LLM. | `agents/guardrails.py` | High | **PII Redaction Engine**: Pre-execution regex filters automatically scrub Indian Aadhaar numbers (`\d{4}\s\d{4}\s\d{4}`), phone numbers, and emails before LLM dispatch. |
| **Information Disclosure** | Exposure of internal API errors, database schemas, or stack traces in responses. | `backend/app/main.py` | Medium | **Flat Exception Handler & Security Headers**: Sanitized error messages, Strict-Transport-Security (HSTS), Content-Security-Policy (CSP), and X-Frame-Options: DENY. |
| **Information Disclosure** | Data exposure at rest in S3 or RDS. | `infra/terraform/` | High | **AWS KMS Encryption**: S3 SSE-KMS, RDS volume encryption, ElastiCache in-transit (TLS) and at-rest encryption enabled. |
| **Denial of Service** | High-volume query flood exhausting LLM token budget or backend connection pool. | `agents/gateway.py` | High | **Token Budgeting & Fallback**: Token tracking per site, model fallback from primary to secondary provider, and Redis connection pool rate limiting. |
| **Elevation of Privilege** | Untrained operator requests instructions to bypass emergency shutdown (ESD) interlocks. | `agents/guardrails.py` | Critical | **Industrial Safety Guardrails**: Pre-execution filters intercept and block attempts to override safety valves (PSVs), bypass ESD trips, or silence fire alarms, citing OISD-156. |
| **Elevation of Privilege** | Low-privilege operator attempting to create automation policies or review approvals. | `backend/app/core/auth.py` | High | **Role-Based Access Control**: `require_roles([AppRole.AUTOMATION_ADMIN, AppRole.PLANT_MANAGER])` enforced on administrative routes. |

---

## 2. Process Safety Boundary Constraint

> [!CAUTION]
> **Direct Industrial-Control Prohibition**:
> AuRAG is permanently restricted to enterprise-tier workflow systems (SAP PM work-order drafts, QMS non-conformance records, and operator notifications). Direct control system writes (DCS, PLC, SCADA) are physically and logically segregated by unidirectional data diodes and firewall rules.
