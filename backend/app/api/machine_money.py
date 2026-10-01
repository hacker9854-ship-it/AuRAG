"""FastAPI router for Machine Money endpoints (payment intents, invoices, quotes, and audit)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.neo4j import get_session
from backend.app.db.database import get_db
from backend.app.services.machine_money.registry import generate_idempotency_key
from backend.app.services.machine_money.schemas import (
    InvoiceRequest,
    JudgeExecutionRequest,
    JudgeExecutionResponse,
    PaymentStatus,
    ProviderHealth,
    ServiceQuote,
    SimulationRequest,
    SimulationResult,
)
from backend.app.services.machine_money.service import MachineMoneyService

router = APIRouter(prefix="/machine-money", tags=["machine-money"])
service = MachineMoneyService()


class QuoteRequest(BaseModel):
    equipment_id: str = Field(..., json_schema_extra={"example": "P-101A"})
    service_id: Optional[str] = Field(default=None, description="Registered service ID from demo catalog")
    service_description: Optional[str] = Field(default=None, json_schema_extra={"example": "Bearing replacement and laser alignment"})
    cost_sats: Optional[int] = Field(default=None, gt=0)


class PayInvoiceRequest(BaseModel):
    bolt11: str = Field(..., description="BOLT11 payment request string")
    amount_sats: int = Field(..., gt=0, description="Amount in satoshis")
    work_order_id: Optional[str] = None
    event_id: Optional[str] = None
    quote_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    bypass_policy: bool = False
    vendor_name: Optional[str] = None
    confidence: Optional[float] = 0.95


class ApprovePaymentRequest(BaseModel):
    reviewer_id: str = Field(default="operator-lead", description="Identifier of approving plant engineer")
    review_notes: Optional[str] = Field(default=None, description="Operational sign-off rationale")


@router.get("/health", response_model=ProviderHealth)
async def machine_money_health():
    """Verify Machine Money subsystem status and configured payment provider."""
    return await service.get_health()


@router.get("/providers")
def get_providers():
    """List registered demo service providers and verifiable service specifications (Section 12)."""
    return service.get_providers_and_services()


@router.post("/quote", response_model=ServiceQuote)
def request_service_quote(req: QuoteRequest):
    """Request a verifiable service quote for equipment maintenance."""
    return service.generate_quote(
        equipment_id=req.equipment_id,
        service_description=req.service_description,
        cost_sats=req.cost_sats,
        service_id=req.service_id,
    )


@router.post("/invoice")
async def create_invoice(req: InvoiceRequest, db: Session = Depends(get_db)):
    """Generate a Lightning invoice and register a pending payment record."""
    try:
        if not req.idempotency_key and req.equipment_id and req.event_id:
            req.idempotency_key = generate_idempotency_key(
                site_id="plant-mumbai-01",
                equipment_id=req.equipment_id,
                service_id=req.memo[:24],
                predictive_event_id=req.event_id,
            )
        record = await service.create_invoice(db, req)
        return record.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/pay")
async def pay_invoice(req: PayInvoiceRequest, db: Session = Depends(get_db)):
    """Execute a Lightning payment under automated spending policy governance."""
    try:
        record = await service.execute_payment(
            db=db,
            bolt11=req.bolt11,
            amount_sats=req.amount_sats,
            work_order_id=req.work_order_id,
            event_id=req.event_id,
            quote_id=req.quote_id,
            idempotency_key=req.idempotency_key,
            bypass_policy=req.bypass_policy,
            vendor_name=req.vendor_name,
            confidence=req.confidence if req.confidence is not None else 0.95,
        )
        return record.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/payments")
def list_payments(limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db)):
    """List recent Machine Money settlement records."""
    records = service.list_payments(db, limit=limit)
    return [r.to_dict() for r in records]


@router.get("/payments/{payment_id}")
def get_payment(payment_id: str, db: Session = Depends(get_db)):
    """Fetch details of a specific payment by its payment_id."""
    record = service.get_payment(db, payment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return record.to_dict()


@router.post("/payments/{payment_id}/approve")
async def approve_payment(
    payment_id: str,
    req: Optional[ApprovePaymentRequest] = None,
    db: Session = Depends(get_db),
    neo4j_session = Depends(get_session),
):
    """Operator human-in-the-loop sign-off to execute a payment previously held in approval queue."""
    reviewer = req.reviewer_id if req else "operator-lead"
    notes = req.review_notes if req else None
    try:
        record = await service.approve_payment(
            db=db,
            payment_id=payment_id,
            reviewer_id=reviewer,
            review_notes=notes,
            neo4j_session=neo4j_session,
        )
        return record.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/simulate", response_model=SimulationResult)
def simulate_m2m_transaction(req: SimulationRequest, db: Session = Depends(get_db)):
    """Dry-run simulation of M2M transaction workflow without mutating state or moving funds."""
    try:
        return service.simulate_m2m_transaction(db, req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/payments/{payment_id}/trail")
def get_payment_trail(
    payment_id: str,
    db: Session = Depends(get_db),
    neo4j_session = Depends(get_session),
):
    """Retrieve operational evidence graph trail explaining why this payment was made."""
    return service.get_payment_trail(db, payment_id, neo4j_session=neo4j_session)


class TelemetryTriggerRequest(BaseModel):
    equipment_tag: str = Field(default="P-101A", description="Equipment identifier")
    event_id: Optional[str] = Field(default="EVT-VIB-001", description="Predictive event identifier")
    failure_event_id: Optional[str] = Field(default="FE-001", description="Matched failure signature")
    confidence: float = Field(default=0.94, ge=0.0, le=1.0)
    work_order_id: Optional[str] = Field(default="WO-2026-P101")
    bypass_policy: bool = False


class AgentPaymentProposal(BaseModel):
    action: str = Field(default="PAY_FOR_SERVICE", description="Must be 'PAY_FOR_SERVICE'")
    service_id: str = Field(default="bearing-inspection", description="Target service from catalog")
    equipment_tag: str = Field(default="P-101A", description="Equipment tag")
    reason: str = Field(default="High-confidence vibration excursion matches FE-001")
    evidence: List[str] = Field(default_factory=lambda: ["FE-001", "WO-1002", "PROC-001"])
    confidence: float = Field(default=0.94, ge=0.0, le=1.0)
    event_id: Optional[str] = None
    work_order_id: Optional[str] = None


@router.post("/trigger-from-telemetry")
async def trigger_from_telemetry(
    req: TelemetryTriggerRequest,
    db: Session = Depends(get_db),
    neo4j_session = Depends(get_session),
):
    """Autonomous bridge: triggers quote -> policy -> invoice -> settlement from predictive telemetry (Section 16)."""
    try:
        from backend.app.services.machine_money.bridge import trigger_m2m_settlement_for_event
        return await trigger_m2m_settlement_for_event(
            db=db,
            equipment_tag=req.equipment_tag,
            event_id=req.event_id,
            failure_event_id=req.failure_event_id,
            confidence=req.confidence,
            work_order_id=req.work_order_id,
            bypass_policy=req.bypass_policy,
            neo4j_session=neo4j_session,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/agent-tool")
async def agent_payment_tool(
    proposal: AgentPaymentProposal,
    db: Session = Depends(get_db),
    neo4j_session = Depends(get_session),
):
    """Governed agent action boundary: LLM proposes service payment, backend policy engine enforces (Section 17)."""
    try:
        from backend.app.services.machine_money.bridge import handle_agent_payment_proposal
        return await handle_agent_payment_proposal(
            db=db,
            proposal=proposal.model_dump(),
            neo4j_session=neo4j_session,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/evidence/{payment_id}")
def get_payment_evidence_package(payment_id: str, db: Session = Depends(get_db)):
    """Retrieve structured cross-layer evidence package answering 'Why did the agent spend money?' (Section 18)."""
    record = service.get_payment(db, payment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Payment record not found")

    import json
    meta = json.loads(record.metadata_json) if record.metadata_json else {}
    evidence = meta.get("evidence_package")
    if not evidence:
        from backend.app.services.machine_money.bridge import build_operational_evidence_package
        evidence = build_operational_evidence_package(
            session=None,
            equipment_tag=meta.get("equipment_id", "P-101A"),
            event_id=record.predictive_event_id,
        )

    return {
        "payment_id": payment_id,
        "amount_sats": record.amount_sats,
        "status": record.status,
        "paid_at": record.paid_at.isoformat() if record.paid_at else None,
        "evidence_package": evidence,
    }


@router.get("/payments/{payment_id}/proof-package")
async def get_payment_proof_package(
    payment_id: str,
    db: Session = Depends(get_db),
    neo4j_session = Depends(get_session),
):
    """BE-04: Retrieve complete structured proof package (non-secret audit records, preimage proof, policy, and graph links)."""
    try:
        return await service.get_proof_package(db=db, payment_id=payment_id, neo4j_session=neo4j_session)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/judge/execute", response_model=JudgeExecutionResponse)
async def execute_judge_mode(
    req: Optional[JudgeExecutionRequest] = None,
    db: Session = Depends(get_db),
    neo4j_session = Depends(get_session),
):
    """Execute complete deterministic Judge Mode scenario with measured stage timings."""
    payload = req or JudgeExecutionRequest()
    try:
        return await service.execute_judge_scenario(
            db=db,
            scenario=payload.scenario,
            equipment_id=payload.equipment_id,
            override_cost_sats=payload.override_cost_sats,
            auto_approve=payload.auto_approve,
            neo4j_session=neo4j_session,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/judge/reset")
async def reset_judge_mode():
    """Reset Judge Mode demonstration state without clearing unrelated historical records."""
    health = await service.get_health()
    return {
        "status": "RESET",
        "message": "Judge Mode demo scenario reset to baseline ready state.",
        "provider": health.provider_name,
        "network": health.network,
        "ready": True,
    }



