"""Provider-neutral payment boundary. No provider means no checkout and never success."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import hmac
import re
from typing import Protocol


class PaymentNotConfigured(RuntimeError):
    """Raised when no real payment provider is configured."""


class PaymentValidationError(ValueError):
    """Raised when a payment request contains an invalid amount or currency."""


@dataclass(frozen=True)
class PaymentIntentRequest:
    transaction_id: int
    amount: Decimal
    currency: str
    idempotency_key: str


@dataclass(frozen=True)
class PaymentIntentResult:
    provider: str
    provider_intent_id: str
    checkout_url: str
    status: str


class PaymentProvider(Protocol):
    @property
    def ready(self) -> bool: ...

    def create_intent(self, request: PaymentIntentRequest) -> PaymentIntentResult: ...


def validate_payment_request(request: PaymentIntentRequest) -> PaymentIntentRequest:
    """Validate server-derived transaction values before calling a payment provider."""
    if isinstance(request.transaction_id, bool) or not isinstance(request.transaction_id, int) or request.transaction_id < 1:
        raise PaymentValidationError("Transaction ID must be a positive integer.")
    try:
        amount = Decimal(str(request.amount))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise PaymentValidationError("Amount must be a valid decimal value.") from exc
    if not amount.is_finite() or amount <= 0:
        raise PaymentValidationError("Amount must be greater than zero.")
    if amount.as_tuple().exponent < -2:
        raise PaymentValidationError("Amount must have at most two decimal places.")
    # Match the marketplace's Numeric(12, 2) money columns and avoid overflow
    # when normalizing extremely large Decimal values.
    if amount.adjusted() > 9:
        raise PaymentValidationError("Amount exceeds the supported transaction limit.")
    if not isinstance(request.currency, str):
        raise PaymentValidationError("Currency must be a three-letter ISO-style code.")
    currency = request.currency.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise PaymentValidationError("Currency must be a three-letter ISO-style code.")
    if not isinstance(request.idempotency_key, str):
        raise PaymentValidationError("Idempotency key must contain 1–128 characters.")
    key = request.idempotency_key.strip()
    if not key or len(key) > 128:
        raise PaymentValidationError("Idempotency key must contain 1–128 characters.")
    try:
        normalized_amount = amount.quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise PaymentValidationError("Amount cannot be represented as a supported transaction value.") from exc
    return PaymentIntentRequest(
        transaction_id=request.transaction_id,
        amount=normalized_amount,
        currency=currency,
        idempotency_key=key,
    )


class DisabledPaymentProvider:
    """Safe default: explicitly unavailable and incapable of reporting success."""

    name = "disabled"

    @property
    def ready(self) -> bool:
        return False

    def create_intent(self, request: PaymentIntentRequest) -> PaymentIntentResult:
        validate_payment_request(request)
        raise PaymentNotConfigured(
            "Payment processing is disabled. Configure and verify a real provider before checkout."
        )


def verify_webhook_signature(raw_body: bytes, supplied_signature: str, secret: str) -> bool:
    """Verify a hex HMAC-SHA256 signature over the exact raw webhook body."""
    if not isinstance(raw_body, bytes) or not isinstance(supplied_signature, str) or not isinstance(secret, str):
        return False
    if not secret or not supplied_signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    candidate = supplied_signature.strip()
    if candidate.startswith("sha256="):
        candidate = candidate[7:]
    candidate = candidate.lower()
    # Reject malformed/non-ASCII input before compare_digest so invalid signatures fail closed.
    if not re.fullmatch(r"[0-9a-f]{64}", candidate):
        return False
    return hmac.compare_digest(expected, candidate)
