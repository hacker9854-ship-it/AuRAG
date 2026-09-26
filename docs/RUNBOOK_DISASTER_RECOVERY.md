# AuRAG Disaster Recovery & Business Continuity Runbook

## 1. Objectives & Service Level Indicators
* **Recovery Point Objective (RPO)**: $\le 1$ hour (maximum acceptable data loss window).
* **Recovery Time Objective (RTO)**: $\le 4$ hours (maximum acceptable downtime to full restoration).
* **Backup Frequency**: Automated continuous WAL archiving + daily automated snapshots at 19:00 UTC (00:30 IST) with 30-day retention.

---

## 2. Disaster Scenarios & Recovery Playbooks

### Scenario A: Availability Zone (AZ) Hardware Failure
* **Symptoms**: Sudden loss of health probes in `ap-south-1a`, latency spike on backend tasks.
* **Automated Action**:
  1. AWS RDS PostgreSQL initiates automated Multi-AZ failover to `ap-south-1b` (synchronous replica promoted in <60 seconds).
  2. Application Load Balancer detects unhealthy target group members in AZ-a and shifts 100% of traffic to healthy tasks in AZ-b.
  3. ECS Fargate automatically re-provisions replacement tasks in AZ-b.
* **Operator Verification**:
  ```bash
  python scripts/health_probe.py --url https://aurag.plant-mumbai.internal
  ```

---

### Scenario B: Accidental Bulk Corruption or Malformed Automation
* **Symptoms**: Erroneous work orders or corrupted metadata staged across relational tables.
* **Recovery Procedure**:
  1. Place AuRAG into Maintenance Mode:
     ```bash
     aws ecs update-service --cluster aurag-production-cluster --service aurag-production-backend-service --desired-count 0
     ```
  2. Locate the most recent verified point-in-time snapshot bundle in `data/backups/` or Amazon S3:
     ```bash
     python scripts/backup_restore.py --action verify --bundle-dir data/backups/aurag_backup_plant-mumbai-01_YYYYMMDDTHHMMSSZ
     ```
  3. Restore database tables from verified snapshot:
     ```bash
     python scripts/backup_restore.py --action restore --bundle-dir data/backups/aurag_backup_plant-mumbai-01_YYYYMMDDTHHMMSSZ
     ```
  4. Run the automated DR verification drill to validate table row counts and SHA256 parity:
     ```bash
     python scripts/disaster_recovery_drill.py
     ```
  5. Restart backend services:
     ```bash
     aws ecs update-service --cluster aurag-production-cluster --service aurag-production-backend-service --desired-count 2
     ```

---

### Scenario C: Complete Cloud Outage / Catastrophic Failover
* **Symptoms**: Total loss of primary VPC resources or cloud provider regional outage.
* **Recovery Procedure**:
  1. Provision standby infrastructure using Terraform:
     ```bash
     cd infra/terraform
     terraform init
     terraform apply -var="environment=dr-standby" -auto-approve
     ```
  2. Pull latest replicated backup bundle from secondary region S3 replica.
  3. Restore database schema and records using `scripts/backup_restore.py`.
  4. Point DNS CNAME to the newly created ALB DNS name exported by Terraform.
  5. Run `python scripts/health_probe.py` to confirm 100% green health across all dependencies.

---

## 3. Post-Incident Review Checklist
- [ ] Confirm zero cross-site data leakage.
- [ ] Verify SHA256 cryptographic checksum parity across all restored tables.
- [ ] Verify Entra ID authentication and role bindings.
- [ ] Record actual RTO and RPO in the postmortem log.
- [ ] Schedule blameless engineering postmortem within 48 hours.
