"""Automated tests for deployment IaC, disaster recovery drills, and health probes."""
import json
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.database import Base
from backend.app.db.models import (
    ApprovalRecord,
    AuditEvent,
    AutomationPolicy,
    ConnectorSync,
    EvaluationRemediation,
    QuarantineItem,
)
from scripts.backup_restore import create_backup, restore_backup, verify_backup
from scripts.disaster_recovery_drill import execute_dr_drill
from scripts.health_probe import check_http_endpoint


@pytest.fixture
def populated_test_db(tmp_path):
    db_file = tmp_path / "source_test.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()

    # Seed records across tables
    session.add(AuditEvent(user_id="user1", site_id="plant-mumbai-01", role="Operator", action_type="QUERY", status="SUCCESS"))
    session.add(ApprovalRecord(action_type="WORK_ORDER_WRITE", target_system="SAP_PM", payload_json="{}", requested_by="user1", site_id="plant-mumbai-01"))
    session.add(AutomationPolicy(policy_id="POL-TEST", site_id="plant-mumbai-01", name="Test Policy", trigger_type="TEST", action_type="TEST", target_system="TEST"))
    session.add(ConnectorSync(connector_id="sap_pm", source_type="SAP_PM", site_id="plant-mumbai-01", status="HEALTHY"))
    session.add(QuarantineItem(source_system="SharePoint", filename="corrupt.pdf", sha256="abc12345", quarantine_reason="Invalid header"))
    session.add(EvaluationRemediation(score_id="SCORE-1", user_id="user1", site_id="plant-mumbai-01", reason="Low faith", correction_notes="Fixed notes"))
    session.commit()
    session.close()

    return db_url


def test_backup_and_restore_cycle(populated_test_db, tmp_path):
    backup_dir = tmp_path / "backups"

    # 1. Create backup
    manifest = create_backup(populated_test_db, backup_dir, site_id="plant-mumbai-01")
    assert manifest["total_records"] == 6
    assert "audit_events" in manifest["tables"]

    bundle_dir = backup_dir / manifest["backup_id"]
    assert (bundle_dir / "manifest.json").exists()

    # 2. Verify backup checksums
    verification = verify_backup(bundle_dir)
    assert verification["valid"] is True
    assert len(verification["errors"]) == 0

    # 3. Restore into empty target DB
    target_db_url = f"sqlite:///{tmp_path / 'restored.db'}"
    restore_res = restore_backup(bundle_dir, target_db_url)
    assert restore_res["status"] == "SUCCESS"
    assert restore_res["restored"]["audit_events"] == 1
    assert restore_res["restored"]["automation_policies"] == 1

    # 4. Verify target DB has records
    target_engine = create_engine(target_db_url)
    TargetSession = sessionmaker(bind=target_engine)
    target_session = TargetSession()
    assert target_session.query(AuditEvent).count() == 1
    assert target_session.query(AutomationPolicy).count() == 1
    target_session.close()


def test_disaster_recovery_drill_execution(populated_test_db, tmp_path):
    drill_dir = tmp_path / "dr_drill"
    report = execute_dr_drill(source_db_url=populated_test_db, drill_output_dir=drill_dir)

    assert report["status"] == "PASSED"
    assert report["rto_achieved"] is True
    assert report["total_entities_restored"] == 6
    assert report["checksum_verification"] == "VERIFIED_VALID"
    assert (drill_dir / "dr_drill_report.json").exists()


def test_health_probe_endpoint_logic():
    # Probe an unreachable URL to test failure handling
    bad_res = check_http_endpoint("http://127.0.0.1:59999/nonexistent", timeout_seconds=0.5)
    assert bad_res["healthy"] is False
    assert bad_res["status_code"] == 0 or bad_res["status_code"] >= 400


def test_terraform_files_syntax_and_structure():
    tf_dir = Path(__file__).resolve().parents[2] / "infra" / "terraform"
    assert tf_dir.exists()

    required_files = [
        "main.tf",
        "variables.tf",
        "outputs.tf",
        "ecs.tf",
        "rds.tf",
        "elasticache.tf",
        "s3.tf",
        "iam.tf",
    ]

    for fname in required_files:
        fpath = tf_dir / fname
        assert fpath.exists(), f"Missing Terraform file: {fname}"
        content = fpath.read_text(encoding="utf-8")
        assert len(content.strip()) > 50, f"File {fname} appears empty or truncated"

    # Validate key resource declarations
    main_content = (tf_dir / "main.tf").read_text(encoding="utf-8")
    assert 'resource "aws_vpc"' in main_content
    assert 'resource "aws_nat_gateway"' in main_content

    ecs_content = (tf_dir / "ecs.tf").read_text(encoding="utf-8")
    assert 'resource "aws_ecs_cluster"' in ecs_content
    assert 'resource "aws_lb"' in ecs_content

    rds_content = (tf_dir / "rds.tf").read_text(encoding="utf-8")
    assert 'resource "aws_db_instance"' in rds_content
