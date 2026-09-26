"""Machine Money business domain service: Coordinates quotes, invoices, policy checks,
settlement, and audit persistence.
"""
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.db.models import ApprovalRecord, AuditEvent, AutomationPolicy, PaymentRecord, utcnow
from backend.app.services.machine_money.exceptions import (
    DuplicatePaymentError,
    MachineMoneyError,
    PolicyViolationError,
    SpendingLimitExceededError,
)
from backend.app.services.machine_money.providers import get_payment_provider
from backend.app.services.machine_money.schemas import (
    BOLT11Invoice,
    InvoiceRequest,
    PaymentReceipt,
    PaymentStatus,
    ProviderHealth,
    ServiceQuote,
)

logger = logging.getLogger(__name__)


class MachineMoneyService:
    """Orchestrates machine-to-machine Bitcoin Lightning settlements with strict policy controls."""

    def __init__(self):
        self.provider = get_payment_provider()

    async def get_health(self) -> ProviderHealth:
        """Query health and readiness of the underlying Lightning settlement rail."""
        return await self.provider.health()

    def generate_quote(
        self,
        equipment_id: str,
        service_description: str,
        cost_sats: int = 150,
        vendor_name: str = "Industrial Dynamics Specialist Node",
    ) -> ServiceQuote:
        """Create a verifiable maintenance service quotation for an operational need."""
        now = utcnow()
        quote_id = f"QTE-{uuid.uuid4().hex[:8].upper()}"
        return ServiceQuote(
            quote_id=quote_id,
            vendor_node_id=f"03vendor{uuid.uuid4().hex[:20]}",
            vendor_name=vendor_name,
            equipment_id=equipment_id,
            service_description=service_description,
            cost_sats=cost_sats,
            estimated_duration_hours=2.5,
            parts_included=["bearing_assembly_6205", "high_temp_synthetic_grease", "vibration_gasket"],
            created_at=now,
            valid_until=now + timedelta(hours=24),
        )

    async def create_invoice(self, db: Session, request: InvoiceRequest) -> PaymentRecord:
        """Generate a Lightning BOLT11 invoice and persist a pending PaymentRecord in the database."""
        # Check idempotency if key provided
        if request.idempotency_key:
            existing = db.query(PaymentRecord).filter(
                PaymentRecord.idempotency_key == request.idempotency_key
            ).first()
            if existing:
                return existing

        invoice = await self.provider.create_invoice(request)
        provider_name = os.environ.get("MACHINE_MONEY_PROVIDER", "mock")
        network = os.environ.get("MACHINE_MONEY_NETWORK", "regtest")

        record = PaymentRecord(
            payment_id=f"PAY-{uuid.uuid4().hex[:12]}",
            provider=provider_name,
            network=network,
            status=PaymentStatus.INVOICE_CREATED.value,
            invoice=invoice.payment_request,
            payment_hash=invoice.payment_hash,
            amount_sats=request.amount_sats,
            amount_msat=request.amount_sats * 1000,
            work_order_id=request.work_order_id,
            predictive_event_id=request.event_id,
            idempotency_key=request.idempotency_key,
            metadata_json=json.dumps({
                "memo": request.memo,
                "equipment_id": request.equipment_id,
                "expires_at": invoice.expires_at.isoformat(),
            }),
        )

        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    async def execute_payment(
        self,
        db: Session,
        bolt11: str,
        amount_sats: int,
        work_order_id: Optional[str] = None,
        event_id: Optional[str] = None,
        quote_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        bypass_policy: bool = False,
    ) -> PaymentRecord:
        """Evaluate spending governance and execute Lightning payment if within autonomous limits."""
        # 1. Idempotency Check
        if idempotency_key:
            existing = db.query(PaymentRecord).filter(
                PaymentRecord.idempotency_key == idempotency_key
            ).first()
            if existing and existing.status in (PaymentStatus.SETTLED.value, PaymentStatus.MOCK_PAID.value):
                logger.info(f"Payment already settled for idempotency key {idempotency_key}")
                return existing

        # 2. Programmatic Spending Policy Check
        max_autopay = int(os.environ.get("MACHINE_MONEY_MAX_AUTOPAY_SATS", "500"))
        autopay_enabled = os.environ.get("MACHINE_MONEY_AUTO_PAY_ENABLED", "false").lower() == "true"

        requires_human_approval = not bypass_policy and (
            not autopay_enabled or amount_sats > max_autopay
        )

        provider_name = os.environ.get("MACHINE_MONEY_PROVIDER", "mock")
        network = os.environ.get("MACHINE_MONEY_NETWORK", "regtest")

        if requires_human_approval:
            # Create an ApprovalRecord in the existing governance ledger
            approval_id = f"APP-PAY-{uuid.uuid4().hex[:8]}"
            approval = ApprovalRecord(
                approval_id=approval_id,
                action_type="EXECUTE_LIGHTNING_PAYMENT",
                target_system="MACHINE_MONEY_LIGHTNING",
                payload_json=json.dumps({
                    "amount_sats": amount_sats,
                    "bolt11": bolt11,
                    "work_order_id": work_order_id,
                    "event_id": event_id,
                    "quote_id": quote_id,
                }),
                requested_by="ai-agent-supervisor",
                site_id="plant-mumbai-01",
                status="PENDING",
                rollback_guidance="Do not execute payment transaction; cancel vendor quote.",
            )
            db.add(approval)

            record = PaymentRecord(
                payment_id=f"PAY-{uuid.uuid4().hex[:12]}",
                provider=provider_name,
                network=network,
                status=PaymentStatus.PENDING_APPROVAL.value,
                invoice=bolt11,
                amount_sats=amount_sats,
                amount_msat=amount_sats * 1000,
                work_order_id=work_order_id,
                predictive_event_id=event_id,
                quote_id=quote_id,
                approval_id=approval_id,
                idempotency_key=idempotency_key,
                metadata_json=json.dumps({"reason": "Spending policy requires human approval"}),
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

        # 3. Autonomous Execution via Provider
        try:
            receipt = await self.provider.pay_invoice(bolt11)
            final_status = receipt.status.value
            preimage = receipt.preimage
            payment_hash = receipt.payment_hash
            fee_sats = receipt.fee_sats
        except Exception as exc:
            logger.error(f"Lightning payment failed: {exc}")
            record = PaymentRecord(
                payment_id=f"PAY-{uuid.uuid4().hex[:12]}",
                provider=provider_name,
                network=network,
                status=PaymentStatus.FAILED.value,
                invoice=bolt11,
                amount_sats=amount_sats,
                amount_msat=amount_sats * 1000,
                work_order_id=work_order_id,
                predictive_event_id=event_id,
                error_code="PROVIDER_PAY_FAILED",
                error_message=str(exc),
                idempotency_key=idempotency_key,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

        # 4. Save Settled Record & Audit Event
        record = PaymentRecord(
            payment_id=f"PAY-{uuid.uuid4().hex[:12]}",
            provider=provider_name,
            network=network,
            status=final_status,
            invoice=bolt11,
            payment_hash=payment_hash,
            preimage=preimage,
            amount_sats=amount_sats,
            amount_msat=amount_sats * 1000,
            fee_sats=fee_sats,
            fee_msat=fee_sats * 1000,
            work_order_id=work_order_id,
            predictive_event_id=event_id,
            quote_id=quote_id,
            idempotency_key=idempotency_key,
            paid_at=utcnow(),
            metadata_json=json.dumps({
                "settled_at": receipt.settled_at.isoformat(),
                "receipt_id": receipt.receipt_id,
            }),
        )
        db.add(record)

        # Write immutable audit event
        audit = AuditEvent(
            event_id=f"AUDIT-PAY-{uuid.uuid4().hex[:10]}",
            user_id="ai-agent-supervisor",
            site_id="plant-mumbai-01",
            role="AUTONOMOUS_AGENT",
            action_type="LIGHTNING_PAYMENT_SETTLED",
            resource_type="WORK_ORDER",
            resource_id=work_order_id or "WO-UNKNOWN",
            details_json=json.dumps({
                "payment_id": record.payment_id,
                "amount_sats": amount_sats,
                "payment_hash": payment_hash,
                "preimage": preimage,
                "provider": provider_name,
            }),
            status="SUCCESS",
        )
        db.add(audit)

        db.commit()
        db.refresh(record)
        return record

    def get_payment(self, db: Session, payment_id: str) -> Optional[PaymentRecord]:
        """Fetch payment record by primary payment ID."""
        return db.query(PaymentRecord).filter(PaymentRecord.payment_id == payment_id).first()

    def list_payments(self, db: Session, limit: int = 50) -> List[PaymentRecord]:
        """List chronological history of Machine Money transactions."""
        return (
            db.query(PaymentRecord)
            .order_by(PaymentRecord.created_at.desc())
            .limit(limit)
            .all()
        )
