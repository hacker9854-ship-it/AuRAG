"""Domain exceptions for the Machine Money payment and settlement subsystem."""

class MachineMoneyError(Exception):
    """Base exception for all Machine Money operations."""
    pass


class ProviderError(MachineMoneyError):
    """Raised when an external Lightning provider fails to communicate or execute."""
    pass


class PolicyViolationError(MachineMoneyError):
    """Raised when a payment request violates plant automation spending governance."""
    pass


class SpendingLimitExceededError(PolicyViolationError):
    """Raised when an autonomous payment exceeds the permitted satoshi threshold."""
    def __init__(self, amount_sats: int, max_allowed_sats: int):
        self.amount_sats = amount_sats
        self.max_allowed_sats = max_allowed_sats
        super().__init__(
            f"Payment amount {amount_sats} sats exceeds maximum allowed autonomous limit of {max_allowed_sats} sats"
        )


class DuplicatePaymentError(MachineMoneyError):
    """Raised when an idempotent payment key is reused for an already processed transaction."""
    pass


class InvoiceExpiredError(ProviderError):
    """Raised when attempting to pay a BOLT11 invoice that has already expired."""
    pass
