"""Abstract base interface (Protocol) for all Lightning payment providers."""
from abc import ABC, abstractmethod
from typing import Optional
from backend.app.services.machine_money.schemas import (
    InvoiceRequest, BOLT11Invoice, PaymentReceipt, ProviderHealth
)


class LightningProvider(ABC):
    """Abstract payment provider for the Machine Money subsystem.
    Implementations include MockProvider, LNbitsProvider, and CoreLightningProvider.
    """

    @abstractmethod
    async def health(self) -> ProviderHealth:
        """Check provider connectivity, node balance, and network state."""
        pass

    @abstractmethod
    async def create_invoice(self, request: InvoiceRequest) -> BOLT11Invoice:
        """Generate a BOLT11 invoice for receiving payment."""
        pass

    @abstractmethod
    async def pay_invoice(self, bolt11: str, max_fee_sats: int = 20) -> PaymentReceipt:
        """Pay a BOLT11 invoice from the agent's controlled wallet."""
        pass

    @abstractmethod
    async def check_payment(self, payment_hash: str) -> PaymentReceipt:
        """Query settlement status of a previously created or paid invoice."""
        pass
