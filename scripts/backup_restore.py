"""Automated Backup & Restore Utility for AuRAG Enterprise State.

Exports relational audit ledger, automation policies, approval records,
and connector metadata to verifiable JSON snapshot bundles with SHA256 checksums.
"""
import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure repo root is in sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.database import Base, get_database_url
from backend.app.db.models import (
    ApprovalRecord,
    AuditEvent,
    AutomationPolicy,
    ConnectorSync,
    EvaluationRemediation,
    QuarantineItem,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TABLE_MODELS = {
    "audit_events": AuditEvent,
    "approval_records": ApprovalRecord,
    "automation_policies": AutomationPolicy,
    "connector_syncs": ConnectorSync,
    "quarantine_items": QuarantineItem,
    "evaluation_remediations": EvaluationRemediation,
}


def sha256_checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def create_backup(db_url: str, output_dir: Path, site_id: str = "plant-mumbai-01") -> dict:
    """Export all relational tables into a timestamped snapshot bundle."""
    output_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_name = f"aurag_backup_{site_id}_{timestamp}"
    bundle_dir = output_dir / bundle_name
    bundle_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "backup_id": bundle_name,
        "site_id": site_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tables": {},
        "total_records": 0,
    }

    try:
        total_records = 0
        for table_name, model in TABLE_MODELS.items():
            records = session.query(model).all()
            data = [r.to_dict() for r in records]
            serialized = json.dumps(data, indent=2, ensure_ascii=False)
            checksum = sha256_checksum(serialized)

            table_file = bundle_dir / f"{table_name}.json"
            table_file.write_text(serialized, encoding="utf-8")

            manifest["tables"][table_name] = {
                "count": len(data),
                "checksum_sha256": checksum,
                "file": table_file.name,
            }
            total_records += len(data)

        manifest["total_records"] = total_records
        manifest_file = bundle_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        logger.info(f"Successfully created backup {bundle_name} with {total_records} records.")
        return manifest
    finally:
        session.close()


def verify_backup(bundle_dir: Path) -> dict:
    """Verify cryptographic integrity of an exported backup bundle."""
    manifest_file = bundle_dir / "manifest.json"
    if not manifest_file.exists():
        raise FileNotFoundError(f"Manifest not found in {bundle_dir}")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    verification_results = {"valid": True, "errors": []}

    for table_name, meta in manifest.get("tables", {}).items():
        file_path = bundle_dir / meta["file"]
        if not file_path.exists():
            verification_results["valid"] = False
            verification_results["errors"].append(f"Missing file for table {table_name}")
            continue

        content = file_path.read_text(encoding="utf-8")
        current_checksum = sha256_checksum(content)
        if current_checksum != meta["checksum_sha256"]:
            verification_results["valid"] = False
            verification_results["errors"].append(
                f"Checksum mismatch for table {table_name}: expected {meta['checksum_sha256']}, got {current_checksum}"
            )

    return verification_results


def restore_backup(bundle_dir: Path, target_db_url: str) -> dict:
    """Restore table data from a verified snapshot bundle."""
    verification = verify_backup(bundle_dir)
    if not verification["valid"]:
        raise ValueError(f"Backup verification failed: {verification['errors']}")

    manifest_file = bundle_dir / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

    engine = create_engine(target_db_url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    restored_counts = {}
    try:
        # Restore policies first, then syncs, approvals, audits
        restore_order = [
            "automation_policies",
            "connector_syncs",
            "quarantine_items",
            "approval_records",
            "evaluation_remediations",
            "audit_events",
        ]

        for table_name in restore_order:
            if table_name not in manifest["tables"]:
                continue

            file_path = bundle_dir / manifest["tables"][table_name]["file"]
            records_data = json.loads(file_path.read_text(encoding="utf-8"))
            model_cls = TABLE_MODELS[table_name]

            count = 0
            for row in records_data:
                # Handle model fields
                if table_name == "automation_policies":
                    row_clean = {k: v for k, v in row.items() if k not in ("parameters", "created_at", "updated_at")}
                    row_clean["parameters_json"] = json.dumps(row.get("parameters", {}))
                    exists = session.query(model_cls).filter(model_cls.policy_id == row_clean.get("policy_id")).first()
                    if not exists:
                        session.add(model_cls(**row_clean))
                        count += 1
                elif table_name == "approval_records":
                    row_clean = {k: v for k, v in row.items() if k not in ("payload", "created_at", "reviewed_at")}
                    row_clean["payload_json"] = json.dumps(row.get("payload", {}))
                    exists = session.query(model_cls).filter(model_cls.approval_id == row_clean.get("approval_id")).first()
                    if not exists:
                        session.add(model_cls(**row_clean))
                        count += 1
                elif table_name == "audit_events":
                    row_clean = {k: v for k, v in row.items() if k not in ("details", "timestamp")}
                    row_clean["details_json"] = json.dumps(row.get("details", {}))
                    exists = session.query(model_cls).filter(model_cls.event_id == row_clean.get("event_id")).first()
                    if not exists:
                        session.add(model_cls(**row_clean))
                        count += 1
                elif table_name == "evaluation_remediations":
                    row_clean = {k: v for k, v in row.items() if k not in ("incorrect_snippets", "created_at", "resolved_at")}
                    row_clean["incorrect_snippets_json"] = json.dumps(row.get("incorrect_snippets", []))
                    exists = session.query(model_cls).filter(model_cls.remediation_id == row_clean.get("remediation_id")).first()
                    if not exists:
                        session.add(model_cls(**row_clean))
                        count += 1
                else:
                    # Generic import
                    row_clean = {k: v for k, v in row.items() if k not in ("created_at", "last_sync_at")}
                    session.add(model_cls(**row_clean))
                    count += 1

            session.commit()
            restored_counts[table_name] = count

        logger.info(f"Restore complete: {restored_counts}")
        return {"status": "SUCCESS", "restored": restored_counts}
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="AuRAG Backup & Restore Manager")
    parser.add_argument("--action", choices=["backup", "verify", "restore"], default="backup")
    parser.add_argument("--output-dir", type=str, default="data/backups")
    parser.add_argument("--bundle-dir", type=str, help="Directory of backup bundle for verify or restore")
    parser.add_argument("--target-db-url", type=str, default=None)
    args = parser.parse_args()

    db_url = get_database_url()

    if args.action == "backup":
        out = Path(args.output_dir)
        res = create_backup(db_url, out)
        print(json.dumps(res, indent=2))
    elif args.action == "verify":
        if not args.bundle_dir:
            print("Error: --bundle-dir required for verify")
            sys.exit(1)
        res = verify_backup(Path(args.bundle_dir))
        print(json.dumps(res, indent=2))
    elif args.action == "restore":
        if not args.bundle_dir:
            print("Error: --bundle-dir required for restore")
            sys.exit(1)
        target = args.target_db_url or db_url
        res = restore_backup(Path(args.bundle_dir), target)
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
