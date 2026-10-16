import hashlib
import hmac
from decimal import Decimal

import pytest

from backend.app.payment import (
    DisabledPaymentProvider,
    PaymentIntentRequest,
    PaymentNotConfigured,
    PaymentValidationError,
    validate_payment_request,
    verify_webhook_signature,
)


def _request(**overrides):
    values = {
        "transaction_id": 42,
        "amount": Decimal("125.50"),
        "currency": "eur",
        "idempotency_key": "checkout-42",
    }
    values.update(overrides)
    return PaymentIntentRequest(**values)


def test_payment_request_normalizes_currency_and_amount():
    result = validate_payment_request(_request())
    assert result.amount == Decimal("125.50")
    assert result.currency == "EUR"
    assert result.idempotency_key == "checkout-42"


def test_payment_request_accepts_maximum_supported_money_column_value():
    result = validate_payment_request(_request(amount=Decimal("9999999999.99")))
    assert result.amount == Decimal("9999999999.99")


@pytest.mark.parametrize(
    "overrides",
    [
        {"transaction_id": 0},
        {"transaction_id": True},
        {"transaction_id": "42"},
        {"transaction_id": 42.0},
        {"amount": Decimal("10000000000.00")},
        {"amount": Decimal("1e100000")},
        {"amount": Decimal("0")},
        {"amount": Decimal("-1")},
        {"amount": Decimal("1.001")},
        {"amount": Decimal("NaN")},
        {"currency": "EURO"},
        {"currency": None},
        {"currency": "1$"},
        {"idempotency_key": ""},
        {"idempotency_key": None},
        {"idempotency_key": "x" * 129},
    ],
)
def test_payment_request_rejects_invalid_values(overrides):
    with pytest.raises(PaymentValidationError):
        validate_payment_request(_request(**overrides))


def test_disabled_provider_never_reports_success_or_creates_intent():
    provider = DisabledPaymentProvider()
    assert provider.ready is False
    with pytest.raises(PaymentNotConfigured, match="Payment processing is disabled"):
        provider.create_intent(_request())


def test_webhook_signature_accepts_valid_hmac_sha256():
    body = b'{"event":"payment.succeeded","id":"evt_123"}'
    secret = "test-secret"
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(body, signature, secret)
    assert verify_webhook_signature(body, "sha256=" + signature, secret)


def test_webhook_signature_rejects_wrong_body_signature_or_missing_secret():
    body = b'{"event":"payment.succeeded"}'
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert not verify_webhook_signature(body + b" ", signature, "secret")
    assert not verify_webhook_signature(body, "not-a-signature", "secret")
    assert not verify_webhook_signature(body, "é" * 64, "secret")
    assert not verify_webhook_signature(body, "a" * 63, "secret")
    assert not verify_webhook_signature(body, signature, "")
    assert not verify_webhook_signature(body, "", "secret")
