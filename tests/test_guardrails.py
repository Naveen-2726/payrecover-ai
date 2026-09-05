import pytest
import time
from app.safety.guardrails import (
    validate_recovery_guardrails,
    validate_ai_output_schema,
    policy_config
)

def test_guardrails_max_retries_cap():
    is_valid, reason, sanitized = validate_recovery_guardrails(
        transaction_id="tx_max_retry",
        amount=1000.0,
        current_retry_count=3,  # Equal to max limit (3)
        requested_discount_pct=5.0
    )
    assert is_valid is False
    assert "Exceeded maximum allowed retries" in reason

def test_guardrails_cooloff_period():
    now = time.time()
    recent_retry = now - 300  # 5 mins ago (less than 7200s cooloff)
    is_valid, reason, _ = validate_recovery_guardrails(
        transaction_id="tx_cooloff",
        amount=1000.0,
        current_retry_count=1,
        requested_discount_pct=5.0,
        last_retry_timestamp=recent_retry
    )
    assert is_valid is False
    assert "Cool-off period active" in reason

def test_guardrails_discount_capping():
    is_valid, reason, sanitized = validate_recovery_guardrails(
        transaction_id="tx_discount",
        amount=1000.0,
        current_retry_count=0,
        requested_discount_pct=25.0  # Above 10% cap
    )
    assert is_valid is True
    assert sanitized["approved_discount_pct"] == 10.0  # Capped to max 10.0%

def test_ai_output_schema_validation():
    valid_plan = {
        "recommended_action": "SMART_RETRY_NOW",
        "confidence_score": 0.85,
        "rationale": "Bank gateway recovery",
        "cascaded_channels": ["SMART_GATEWAY_RETRY"]
    }
    valid, msg = validate_ai_output_schema(valid_plan)
    assert valid is True

    invalid_plan = {
        "recommended_action": "INVALID_UNAUTHORIZED_ACTION",
        "confidence_score": 1.5,
        "rationale": "test",
        "cascaded_channels": []
    }
    valid, msg = validate_ai_output_schema(invalid_plan)
    assert valid is False
