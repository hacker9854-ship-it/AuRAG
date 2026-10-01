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


class ServiceDefinition(BaseModel):
    service_id: str
    name: str
    provider_id: str
    provider_name: str
    price_sats: int
    equipment_class: str
    description: str
    estimated_duration_hours: float = 2.0
    parts_included: List[str] = Field(default_factory=list)
    is_mock: bool = True


class SimulationRequest(BaseModel):
    site_id: str = "plant-mumbai-01"
    equipment_id: str = "P-101A"
    service_id: Optional[str] = "bearing-inspection"
    predictive_event_id: Optional[str] = "EVT-VIB-001"
    work_order_id: Optional[str] = "WO-2026-P101"
    amount_sats: Optional[int] = None
    confidence: float = 0.94


class SimulationResult(BaseModel):
    dry_run: bool = True
    equipment_id: str
    service_name: str
    amount_sats: int
    idempotency_key: str
    policy_evaluation: Dict[str, Any]
    projected_action: str
    explanation: str


class ExecutionStage(str, Enum):
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    EVIDENCE_MATCHED = "EVIDENCE_MATCHED"
    QUOTE_RESOLVED = "QUOTE_RESOLVED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    INVOICE_GENERATED = "INVOICE_GENERATED"
    PAYMENT_AUTHORIZED = "PAYMENT_AUTHORIZED"
    SETTLEMENT_CONFIRMED = "SETTLEMENT_CONFIRMED"
    GRAPH_LINKED = "GRAPH_LINKED"
    OUTCOME_RESOLVED = "OUTCOME_RESOLVED"


class ExecutionStageEvent(BaseModel):
    stage: ExecutionStage
    status: str = Field(default="SUCCESS", description="SUCCESS, PENDING_APPROVAL, or FAILED")
    elapsed_ms: int = Field(default=0, ge=0, description="Measured elapsed milliseconds from scenario start")
    message: str = Field(..., description="Human-readable explanation of this stage")
    evidence_refs: List[str] = Field(default_factory=list, description="IDs of graph entities or policies cited")
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured non-secret payload")
    timestamp: datetime = Field(default_factory=utcnow)


class JudgeExecutionRequest(BaseModel):
    scenario: str = Field(default="INDUSTRIAL_EMERGENCY", description="INDUSTRIAL_EMERGENCY or POLICY_ESCALATION")
    equipment_id: str = Field(default="P-101A", description="Equipment tag identifier")
    override_cost_sats: Optional[int] = Field(default=None, description="Optional override satoshi amount")
    auto_approve: bool = Field(default=True, description="Whether to auto-pay if under spending cap")


class JudgeExecutionResponse(BaseModel):
    execution_id: str
    scenario: str
    status: str = Field(..., description="SUCCESS, PENDING_APPROVAL, or FAILED")
    total_elapsed_ms: int
    events: List[ExecutionStageEvent]
    payment_record: Optional[Dict[str, Any]] = None
    evidence_package: Optional[Dict[str, Any]] = None
    provider_mode: str = Field(default="MOCK / SIMULATION")
    summary: str

