"""Pydantic schemas for Machine Money entities, invoices, quotes, and payment proofs."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaymentStatus(str, Enum):
    QUOTED = "QUOTED"
    INVOICE_CREATED = "INVOICE_CREATED"
    PENDING = "PENDING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    AUTHORIZED = "AUTHORIZED"
    PAID = "PAID"
    SETTLED = "SETTLED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    REFUNDED = "REFUNDED"
    MOCK_PAID = "MOCK_PAID"


class ProviderHealth(BaseModel):
    provider_name: str
    is_connected: bool
    network: str = "regtest"
    balance_sats: Optional[int] = None
    node_pubkey: Optional[str] = None
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class InvoiceRequest(BaseModel):
    amount_sats: int = Field(gt=0, description="Amount in satoshis")
    memo: str = Field(..., max_length=512, description="Payment memo/purpose")
    work_order_id: Optional[str] = None
    event_id: Optional[str] = None
    equipment_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    expiry_seconds: int = Field(default=3600, ge=60, le=86400)


class BOLT11Invoice(BaseModel):
    invoice_id: str
    payment_hash: str
    payment_request: str  # BOLT11 string
    amount_sats: int
    memo: str
    created_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime
    status: PaymentStatus = PaymentStatus.PENDING


class PaymentReceipt(BaseModel):
    receipt_id: str
    payment_hash: str
    preimage: Optional[str] = None
    amount_sats: int
    fee_sats: int = 0
    provider: str
    status: PaymentStatus
    settled_at: datetime = Field(default_factory=utcnow)
    work_order_id: Optional[str] = None
    event_id: Optional[str] = None
    equipment_id: Optional[str] = None


class ServiceQuote(BaseModel):
    quote_id: str
    vendor_node_id: str
    vendor_name: str
    equipment_id: str
    service_description: str
    cost_sats: int = Field(gt=0)
    estimated_duration_hours: float
    parts_included: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    valid_until: datetime
