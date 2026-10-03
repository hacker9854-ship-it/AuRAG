"""Telemetry-to-Payment Bridge & Agent Action Boundary (Sections 16 - 18).

Connects AuRAG's existing predictive intelligence, failure matching, and GraphRAG
evidence retrieval into the autonomous Lightning micro-settlement layer.
"""
import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.core.neo4j import get_session
from backend.app.db.models import AuditEvent, PaymentRecord, utcnow
from backend.app.services.machine_money.exceptions import MachineMoneyError, PolicyViolationError
from backend.app.services.machine_money.graph import record_payment_in_graph
from backend.app.services.machine_money.registry import (
    generate_idempotency_key,
    get_service,
    list_services,
)
from backend.app.services.machine_money.schemas import (
    InvoiceRequest,
    PaymentStatus,
    ServiceQuote,
)
from backend.app.services.machine_money.service import MachineMoneyService

logger = logging.getLogger(__name__)


def build_operational_evidence_package(
    session,
    equipment_tag: str,
    event_id: Optional[str] = None,
    failure_event_id: Optional[str] = None,
    confidence: float = 0.94,
    vibration_reading: float = 5.4,
    vibration_threshold: float = 4.5,
    data_source_type: Optional[str] = None,
    dataset_name: Optional[str] = None,
    dataset_record_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve operational evidence from Knowledge Graph answering 'Why did the agent spend money?'
    (Section 18 Contract).
    """
    from backend.app.services.machine_money.grounding import get_grounded_evidence_package

    return get_grounded_evidence_package(
        session=session,
        equipment_tag=equipment_tag,
        vibration_reading=vibration_reading,
        vibration_threshold=vibration_threshold,
        event_id=event_id,
        failure_event_id=failure_event_id,
        confidence=confidence,
        data_source_type=data_source_type,
        dataset_name=dataset_name,
        dataset_record_id=dataset_record_id,
    )


def map_telemetry_to_service(
    equipment_tag: str,
    failure_event_id: Optional[str] = None,
    symptom: Optional[str] = None,
) -> str:
    """Map predictive anomaly features to a demo catalog service ID (Section 16)."""
    eq_lower = equipment_tag.lower()
    sym_lower = (symptom or "").lower()

    if "heat" in eq_lower or "exchanger" in eq_lower or "thermal" in sym_lower:
        return "thermal-diagnostics"
    if "compressor" in eq_lower or "oil" in sym_lower or "lube" in sym_lower:
        return "oil-tribology-analysis"
    if "turbine" in eq_lower or "shaft" in sym_lower or "coupling" in sym_lower:
        return "laser-shaft-alignment"
    if "valve" in eq_lower or "prv" in eq_lower or "valve" in sym_lower or "leak" in sym_lower:
        return "valve-integrity-test"

    # Default for P-101 / centrifugal pumps
    return "bearing-inspection"


async def trigger_m2m_settlement_for_event(
    db: Session,
    equipment_tag: str,
    event_id: Optional[str] = None,
    failure_event_id: Optional[str] = None,
    confidence: float = 0.94,
    work_order_id: Optional[str] = None,
    bypass_policy: bool = False,
    neo4j_session = None,
    data_source_type: Optional[str] = None,
    dataset_name: Optional[str] = None,
    dataset_record_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Autonomous end-to-end pipeline:
    PredictiveEvent -> Machine Money Trigger -> Service mapping -> Quote -> Policy -> Invoice -> Payment -> Graph
    (Section 16).
    """
    service = MachineMoneyService()
    evt_id = event_id or "EVT-AUTO-001"
    wo_id = work_order_id or "WO-AUTO-P101"

    # 1. Evidence Extraction
    evidence_package = build_operational_evidence_package(
        session=neo4j_session,
        equipment_tag=equipment_tag,
        event_id=evt_id,
        failure_event_id=failure_event_id,
        confidence=confidence,
        data_source_type=data_source_type,
        dataset_name=dataset_name,
        dataset_record_id=dataset_record_id,
    )

    # 2. Service Mapping
    service_id = map_telemetry_to_service(equipment_tag, failure_event_id)
    svc = get_service(service_id)
    if not svc:
        raise MachineMoneyError(f"Service {service_id} not found in catalog")

    # 3. Generate Quote
    quote = service.generate_quote(
        equipment_id=equipment_tag,
        service_id=service_id,
    )

    # 4. Generate Idempotency Key (Section 14)
    idempotency_key = generate_idempotency_key(
        site_id="plant-mumbai-01",
        equipment_id=equipment_tag,
        service_id=service_id,
        predictive_event_id=evt_id,
    )

    # 5. Check if already settled or pending approval for this idempotency key
    existing = db.query(PaymentRecord).filter(
        PaymentRecord.idempotency_key == idempotency_key
    ).first()
    if existing and existing.status in (
        PaymentStatus.SETTLED.value,
        PaymentStatus.MOCK_PAID.value,
        PaymentStatus.PENDING_APPROVAL.value,
    ):
        logger.info(f"Payment already exists ({existing.status}) for idempotency key {idempotency_key}")
        return {
            "status": existing.status,
            "payment_id": existing.payment_id,
            "idempotency_key": idempotency_key,
            "amount_sats": existing.amount_sats,
            "payment_hash": existing.payment_hash,
            "preimage": existing.preimage,
            "evidence_package": evidence_package,
            "approval_id": existing.approval_id,
            "is_duplicate_prevented": True,
        }

    # 6. Create Lightning Invoice
    invoice_req = InvoiceRequest(
        amount_sats=quote.cost_sats,
        memo=f"M2M Autonomous Settlement: {svc.name} for {equipment_tag}",
        work_order_id=wo_id,
        event_id=evt_id,
        equipment_id=equipment_tag,
        idempotency_key=idempotency_key,
    )
    invoice_record = await service.create_invoice(db, invoice_req)

    # 7. Execute Payment with Policy Evaluation
    payment_record = await service.execute_payment(
        db=db,
        bolt11=invoice_record.invoice,
        amount_sats=quote.cost_sats,
        work_order_id=wo_id,
        event_id=evt_id,
        quote_id=quote.quote_id,
        idempotency_key=idempotency_key,
        bypass_policy=bypass_policy,
        vendor_name=svc.provider_name,
        confidence=confidence,
        neo4j_session=neo4j_session,
    )

    # 8. Enrich Payment Record with Evidence Package
    meta = json.loads(payment_record.metadata_json) if payment_record.metadata_json else {}
    meta["evidence_package"] = evidence_package
    meta["service_id"] = service_id
    meta["vendor_name"] = svc.provider_name
    payment_record.metadata_json = json.dumps(meta)
    db.commit()
    db.refresh(payment_record)

    return {
        "status": payment_record.status,
        "payment_id": payment_record.payment_id,
        "idempotency_key": idempotency_key,
        "amount_sats": payment_record.amount_sats,
        "service": {
            "id": svc.service_id,
            "name": svc.name,
            "provider": svc.provider_name,
        },
        "evidence_package": evidence_package,
        "approval_id": payment_record.approval_id,
        "payment_hash": payment_record.payment_hash,
        "preimage": payment_record.preimage,
        "paid_at": payment_record.paid_at.isoformat() if payment_record.paid_at else None,
        "is_duplicate_prevented": False,
    }


async def handle_agent_payment_proposal(
    db: Session,
    proposal: Dict[str, Any],
    neo4j_session = None,
) -> Dict[str, Any]:
    """Agent tool boundary: LLM proposes structured payment intent, backend policy engine authorizes (Section 17).
    Expected schema:
    {
        "action": "PAY_FOR_SERVICE",
        "service_id": "bearing-inspection",
        "equipment_tag": "P-101A",
        "reason": "High vibration matched FE-001",
        "evidence": ["FE-001", "WO-1002", "PROC-001"],
        "confidence": 0.94
    }
    """
    action = proposal.get("action")
    if action != "PAY_FOR_SERVICE":
        raise MachineMoneyError(f"Unsupported agent action '{action}'. Expected 'PAY_FOR_SERVICE'.")

    service_id = proposal.get("service_id", "bearing-inspection")
    svc = get_service(service_id)
    if not svc:
        raise MachineMoneyError(f"Service '{service_id}' proposed by agent is not in the approved service catalog.")

    equipment_tag = proposal.get("equipment_tag", "P-101A")
    confidence = float(proposal.get("confidence", 0.94))
    evidence = proposal.get("evidence", ["FE-001", "WO-1002", "PROC-001"])
    reason = proposal.get("reason", f"Agent reasoning triggered {svc.name}")

    # Delegate to governed M2M pipeline
    result = await trigger_m2m_settlement_for_event(
        db=db,
        equipment_tag=equipment_tag,
        event_id=proposal.get("event_id", "EVT-AGENT-001"),
        failure_event_id="FE-001" if "FE-001" in evidence else None,
        confidence=confidence,
        work_order_id=proposal.get("work_order_id", "WO-AGENT-101"),
        bypass_policy=False,
        neo4j_session=neo4j_session,
    )
    result["agent_reason"] = reason
    result["agent_proposed_evidence"] = evidence
    return result
