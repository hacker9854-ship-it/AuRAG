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
    provider_mode: str = "MOCK"  # "MOCK" | "LIVE"
    network: str = "regtest"
    settlement_source: str = "SIMULATED"  # "SIMULATED" | "LIGHTNING_NODE"
    is_live: bool = False
    is_connected: bool = True
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
    scenario: str = Field(default="PUBLIC_DATASET_REPLAY", description="PUBLIC_DATASET_REPLAY (NASA IMS Benchmark), INDUSTRIAL_EMERGENCY, POLICY_ESCALATION, or PROVIDER_FAILURE")
    equipment_id: str = Field(default="REPLAY-ASSET-01", description="Equipment tag identifier (defaults to NASA IMS test rig REPLAY-ASSET-01)")
    override_cost_sats: Optional[int] = Field(default=None, description="Optional override satoshi amount")
    auto_approve: bool = Field(default=True, description="Whether to auto-pay if under spending cap")
    confidence: Optional[float] = Field(default=None, description="Diagnostic confidence score (0.0 - 1.0)")


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


class SelectionStrategy(str, Enum):
    FASTEST_SLA = "FASTEST_SLA"
    LOWEST_COST = "LOWEST_COST"
    HIGHEST_RELIABILITY = "HIGHEST_RELIABILITY"
    BALANCED = "BALANCED"


class VendorQuoteCandidate(BaseModel):
    candidate_id: str
    vendor_id: str
    vendor_name: str
    node_pubkey: str
    service_id: str
    service_name: str
    amount_sats: int
    sla_hours: float
    reliability_score: float = Field(..., ge=0.0, le=1.0, description="Reliability score between 0.0 and 1.0")
    reputation_tier: str = Field(default="A", description="AAA, A+, A, B, etc.")
    parts_included: List[str] = Field(default_factory=list)
    bolt11: Optional[str] = Field(default=None, description="Payable BOLT11 Lightning invoice generated by vendor node")
    payment_hash: Optional[str] = Field(default=None, description="BOLT11 payment hash")
    vendor_node_type: str = Field(default="DEMO VENDOR NODE", description="Truthful node classification")
    is_synthetic: bool = True
    within_policy_cap: bool = True
    score: float = 0.0
    valid_until: datetime


class VendorRFQRequest(BaseModel):
    equipment_id: str = Field(default="P-101A", description="Target equipment asset tag")
    service_id: str = Field(default="bearing-inspection", description="Catalog service ID to request bids for")
    strategy: SelectionStrategy = Field(
        default=SelectionStrategy.FASTEST_SLA,
        description="Selection rule: FASTEST_SLA, LOWEST_COST, HIGHEST_RELIABILITY, or BALANCED",
    )
    max_budget_sats: int = Field(default=500, description="Autonomous spending policy cap in satoshis")


class VendorRFQResponse(BaseModel):
    rfq_id: str
    requested_at: datetime
    service_id: str
    equipment_id: str
    strategy: SelectionStrategy
    policy_cap_sats: int
    candidates: List[VendorQuoteCandidate]
    selected_vendor: VendorQuoteCandidate
    selection_rationale: str
    scoring_model: Dict[str, Any]
    is_synthetic: bool = True
    synthetic_disclosure: str = "Synthetic vendor quote model for Bitshala BOSS Battle Machine Money autonomous bidding demonstration"


class JudgeScenarioFixture(BaseModel):
    """Canonical Single-Source-of-Truth Demo Fixture for Bitshala BOSS Battle 2026 (PRD3 Task 2.1)."""
    scenario_id: str = "SCENARIO-BEARING-OVERHEAT-P101A"
    site_id: str = "SITE-TX-401"
    equipment_id: str = "P-101A"
    equipment_name: str = "Slurry Feed Pump P-101A"
    sensor_id: str = "VIB-301-BEARING"
    reading: float = 5.4
    threshold: float = 4.5
    unit: str = "mm/s"
    iso_zone: str = "Zone C (Unrestricted Operation Not Permissible)"
    failure_signature: str = "FE-001"
    failure_title: str = "Bearing inner race spalling & degradation"
    procedure_id: str = "PROC-001"
    procedure_title: str = "High-Frequency Vibration Diagnostics & Bearing Lubrication"
    work_order_id: str = "WO-2026-P101"
    service_type: str = "bearing-inspection"
    canonical_payment_sats: int = 250
    spending_cap_sats: int = 500
    provider_mode: str = "MOCK"
    settlement_source: str = "SIMULATED"
    selected_vendor: str = "Apex Diagnostics"
    selected_vendor_id: str = "apex-diagnostics"
    selected_vendor_pubkey: str = "02" + "a1" * 32
    selection_strategy: str = "BALANCED"
    candidates_count: int = 3


class VendorSpendItem(BaseModel):
    vendor_name: str
    spend_sats: int
    payment_count: int
    percentage: float


class MachineMoneyMetrics(BaseModel):
    total_spend_sats: int = Field(default=0, description="Total satoshis settled across all completed payments")
    total_spend_msat: int = Field(default=0, description="Total milli-satoshis settled")
    total_fee_sats: int = Field(default=0, description="Total routing fees paid in satoshis")
    fiat_spend_usd_estimate: float = Field(default=0.0, description="Estimated fiat USD equivalent (spot estimate)")
    settled_count: int = Field(default=0, description="Number of successfully settled Lightning payments")
    pending_count: int = Field(default=0, description="Number of payments currently pending or awaiting human approval")
    failed_count: int = Field(default=0, description="Number of failed, rejected, or expired payments")
    total_transactions: int = Field(default=0, description="Total payment records in ledger")
    autonomous_count: int = Field(default=0, description="Settled payments approved autonomously within policy cap")
    human_approval_count: int = Field(default=0, description="Payments requiring or completed via human sign-off")
    autonomous_rate_percentage: float = Field(default=0.0, description="Percentage of settlements that were autonomous")
    average_settlement_latency_ms: float = Field(default=0.0, description="Average settlement latency in milliseconds")
    average_settlement_latency_seconds: float = Field(default=0.0, description="Average settlement latency in seconds")
    vendor_spend: List[VendorSpendItem] = Field(default_factory=list, description="Spend breakdown by vendor node")
    total_quotes_generated: int = Field(default=0, description="Total maintenance quotes registered")
    quotes_converted: int = Field(default=0, description="Quotes successfully converted into settled payments")
    quote_to_payment_conversion_rate: float = Field(default=0.0, description="Percentage of quotes converted to settlements (0-100%)")
    computed_at: datetime = Field(default_factory=utcnow)


class IndustrialPlantAssumptions(BaseModel):
    plant_id: str = "plant-mumbai-01"
    equipment_tag: str = "P-101A"
    equipment_name: str = "Heavy Crude Distillation Charge Pump P-101A"
    criticality_tier: str = "TIER_1_CRITICAL"
    hourly_downtime_cost_usd: float = 260000.0
    unmitigated_downtime_hours: float = 4.5
    catastrophic_failure_probability: float = 0.85
    manual_procurement_hours: float = 4.2
    autonomous_m2m_dispatch_seconds: float = 2.1
    default_intervention_sats: int = 250
    btc_fiat_usd_rate: float = 65000.0
    data_basis: str = "Synthetic plant model (Petrochemical refining unit P-101A)"
    assumptions_version: str = "2026.1-synthetic"


class IndustrialEconomicsModel(BaseModel):
    is_estimated: bool = Field(default=True, description="Marker indicating synthetic/modelled calculation")
    estimated_marker: str = Field(default="ESTIMATED_SYNTHETIC_MODEL", description="Standard estimation disclosure")
    calculation_version: str = Field(default="v2026.1-industrial-m2m", description="Version of the calculation engine")
    equipment_tag: str = "P-101A"
    equipment_name: str = "Heavy Crude Distillation Charge Pump P-101A"
    downtime_hours_avoided: float = 4.5
    hourly_downtime_cost_usd: float = 260000.0
    estimated_downtime_exposure_usd: float = 1170000.0
    risk_weighted_exposure_usd: float = 994500.0
    intervention_cost_sats: int = 250
    intervention_cost_usd: float = 0.1625
    net_value_preserved_usd: float = 1169999.84
    protection_multiple: float = 7200000.0
    lead_time_saved_hours: float = 4.2
    assumptions: IndustrialPlantAssumptions = Field(default_factory=IndustrialPlantAssumptions)
    formula: str = "Net Value Preserved = (Avoided Downtime Hours * Hourly Outage Rate) - Intervention Cost USD"
    risk_weighted_formula: str = "Risk-Weighted Exposure = Gross Exposure * Failure Probability Factor"
    data_basis: str = "Synthetic plant model (Petrochemical refining unit P-101A)"
    transparency_notes: str = (
        "Modelled estimate based on synthetic industrial plant assumptions for hackathon demonstration. "
        "All assumptions and formulas are inspectable and customizable."
    )
    computed_at: datetime = Field(default_factory=utcnow)


class IndustrialEconomicsRequest(BaseModel):
    equipment_tag: str = Field(default="P-101A", description="Equipment tag identifier")
    intervention_cost_sats: Optional[int] = Field(default=None, description="Optional override satoshi intervention cost")
    hourly_downtime_cost_usd: Optional[float] = Field(default=None, description="Optional override hourly downtime loss")
    unmitigated_downtime_hours: Optional[float] = Field(default=None, description="Optional override downtime hours")


class HumanApprovalEvidencePackage(BaseModel):
    payment_id: str
    approval_id: str
    status: str = "PENDING_APPROVAL"
    amount_sats: int
    autonomous_cap_sats: int
    excess_sats_over_cap: int
    vendor_name: str
    confidence_percentage: float
    policy_id: str
    policy_reason: str
    equipment_id: str
    equipment_name: str
    failure_event_id: str
    failure_signature: str
    governing_procedure: str
    telemetry_excursion: Dict[str, Any]
    industrial_economics: Dict[str, Any]
    recommended_action: str
    rollback_guidance: str
    created_at: datetime = Field(default_factory=utcnow)





