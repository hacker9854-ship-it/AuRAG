"""FastAPI router for Machine Money endpoints (payment intents, invoices, quotes, and audit)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.services.machine_money.schemas import (
    InvoiceRequest,
    PaymentStatus,
    ProviderHealth,
    ServiceQuote,
)
from backend.app.services.machine_money.service import MachineMoneyService

router = APIRouter(prefix="/machine-money", tags=["machine-money"])
service = MachineMoneyService()


class QuoteRequest(BaseModel):
    equipment_id: str = Field(..., json_schema_extra={"example": "P-101A"})
    service_description: str = Field(..., json_schema_extra={"example": "Bearing replacement and laser alignment"})
    cost_sats: int = Field(default=150, gt=0)


class PayInvoiceRequest(BaseModel):
    bolt11: str = Field(..., description="BOLT11 payment request string")
    amount_sats: int = Field(..., gt=0, description="Amount in satoshis")
    work_order_id: Optional[str] = None
    event_id: Optional[str] = None
    quote_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    bypass_policy: bool = False


@router.get("/health", response_model=ProviderHealth)
async def machine_money_health():
    """Verify Machine Money subsystem status and configured payment provider."""
    return await service.get_health()


@router.post("/quote", response_model=ServiceQuote)
def request_service_quote(req: QuoteRequest):
    """Request a verifiable service quote for equipment maintenance."""
    return service.generate_quote(
        equipment_id=req.equipment_id,
        service_description=req.service_description,
        cost_sats=req.cost_sats,
    )


@router.post("/invoice")
async def create_invoice(req: InvoiceRequest, db: Session = Depends(get_db)):
    """Generate a Lightning invoice and register a pending payment record."""
    try:
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
