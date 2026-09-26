# AuRAG Plant Administrator & Operations Handbook

## 1. Microsoft Entra ID (Azure AD) Registration

To configure enterprise authentication for plant operators and engineers:
1. In the Microsoft Entra admin center, navigate to **Identity > Applications > App registrations**.
2. Create a new registration named `AuRAG-Plant-Operations`.
3. In **App roles**, configure the 7 industrial roles:
   * `PlantOperator` (Operational query access)
   * `ReliabilityEngineer` (Root cause analysis, evaluation remediation)
   * `SafetyInspector` (Statutory compliance rulebooks)
   * `MaintenancePlanner` (Work order staging & approvals)
   * `OperationsLead` (Shift supervisor approvals)
   * `AutomationAdmin` (Automation policy configuration)
   * `PlantManager` (Full administrative governance)
4. Under **Expose an API**, set Application ID URI: `api://aurag-enterprise-app`.
5. Update environment variables on the ECS backend task:
   ```env
   ENTRA_TENANT_ID=<your-tenant-id>
   ENTRA_CLIENT_ID=<your-client-id>
   AUTH_ENABLED=true
   ```

---

## 2. Enterprise Connector Setup & Delta Synchronization

AuRAG continuously synchronizes with plant source systems via `/api/connectors`:

| Connector | Source System | Typical Interval | Sync Type |
|---|---|---|---|
| `sap_pm` | SAP ERP / S4HANA | Every 15 mins | Delta cursor based on modified timestamp |
| `osisoft_pi` | OSIsoft PI Web API | Every 5 mins | Time-series stream with rolling aggregates |
| `sharepoint` | Microsoft 365 SharePoint | Every 60 mins | Microsoft Graph delta token |
| `qms` | Enterprise QMS | Daily | Master standard synchronizer |

### On-Demand Synchronization Trigger:
```bash
curl -X POST http://localhost:8000/api/connectors/sap_pm/sync \
  -H "Authorization: Bearer <JWT>"
```

---

## 3. Automation Policy Administration & Dry-Run Simulator

Plant reliability leads can manage automation rules directly from the **Operations Hub** (`/operations`) or via REST API:

### Policy Parameters:
* `trigger_type`: Event condition (`HEALTH_INDEX_CRITICAL`, `VIBRATION_SPIKE`, `STATUTORY_OVERDUE`).
* `approval_threshold`:
  * `AUTONOMOUS`: System stages work order draft immediately.
  * `REQUIRES_APPROVAL`: Staged draft routed to the Pending Approvals queue for human review.
* `rollback_guidance`: Explicit compensation instructions (e.g. SAP transaction `IW32` cancellation or QMS voiding).

### Testing a Policy with the Dry-Run Simulator:
1. Open **Operations Hub > Dry-Run Policy Simulator**.
2. Select Trigger Type (e.g., `HEALTH_INDEX_CRITICAL`).
3. Set test parameters (e.g., Equipment `P-101A`, Health Index `35`).
4. Click **Run Safe Simulation (Dry-Run)**.
5. Review generated JSON payload and rollback guidance. Verify no database mutations occurred.

---

## 4. Quarantine Review & Human-in-the-Loop Approval

When drawings or SOPs fail integrity checks (malformed PDF, corrupted magic bytes, or checksum mismatch), they are isolated in the Quarantine queue:
1. Navigate to `/operations` (or query `/api/connectors/quarantine`).
2. Review file metadata, quarantine reason, and severity.
3. Click **Approve** (releases file to ingestion pipeline) or **Reject** (permanently drops file with audit event).

---

## 5. Regulatory Compliance & Audit Log Queries

For external statutory audits (State Directorate of Industrial Safety & Health - DISH, or Petroleum & Explosives Safety Organisation - PESO):
* Query the immutable audit ledger:
  ```bash
  curl "http://localhost:8000/api/connectors/audit/events?action_type=APPROVAL_APPROVED&limit=100" \
    -H "Authorization: Bearer <JWT>"
  ```
* Every record includes cryptographic timestamp, verified operator ID, client IP, action payload, and decision notes.
