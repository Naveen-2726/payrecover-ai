import pytest
from app.mock_razorpay.gateway import razorpay_simulator
from app.safety.guardrails import verify_razorpay_signature, check_idempotency

def test_webhook_hmac_signature_generation_and_verification():
    payload, raw_bytes, signature = razorpay_simulator.generate_webhook_payload(
        event_type="payment.failed",
        amount=1999.0,
        bank="HDFC",
        error_code="BAD_REQUEST_PAYMENT_TIMED_OUT"
    )
    assert signature is not None
    assert len(signature) == 64  # SHA-256 hex string length
    
    # Valid signature check
    assert verify_razorpay_signature(raw_bytes, signature) is True
    
    # Tampered signature check
    assert verify_razorpay_signature(raw_bytes, "invalid_signature_string") is False

def test_webhook_idempotency():
    event_id = "evt_test_idempotency_12345"
    assert check_idempotency(event_id) is True
    # Second check with same event ID should fail (duplicate)
    assert check_idempotency(event_id) is False
