import hmac
import hashlib
import time
from typing import Dict, Any, Tuple, Optional, Set

class PolicyConfig:
    def __init__(self):
        self.max_retries_per_transaction: int = 3
        self.min_cooloff_seconds: int = 7200  # 2 hours default
        self.max_discount_percent: float = 10.0  # Max 10% discount cap
        self.min_amount_for_discount: float = 100.0  # Min ₹100 for discount eligibility
        self.max_automated_amount: float = 25000.0
        self.require_webhook_hmac: bool = True
        self.secret_key: str = "rzp_test_secret_payrecover_2026"

policy_config = PolicyConfig()

# In-memory idempotency & lock tracking
_processed_event_ids: Set[str] = set()
_retry_timestamps: Dict[str, list] = {}


def verify_razorpay_signature(raw_body: bytes, signature: str, secret: Optional[str] = None) -> bool:
    """
    Verify Razorpay Webhook HMAC SHA-256 signature using constant-time comparison.
    """
    if not signature:
        return False
    key = (secret or policy_config.secret_key).encode('utf-8')
    expected_sig = hmac.new(key, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_sig, signature)


def check_idempotency(event_id: str) -> bool:
    """
    Check if a webhook event ID has already been processed. Returns True if fresh, False if duplicate.
    """
    if event_id in _processed_event_ids:
        return False
    _processed_event_ids.add(event_id)
    return True


def validate_recovery_guardrails(
    transaction_id: str,
    amount: float,
    current_retry_count: int,
    requested_discount_pct: float,
    last_retry_timestamp: Optional[float] = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluate safety guardrails before executing any recovery action.
    Returns (is_valid, reason, sanitized_parameters).
    """
    # 1. Max retry cap check
    if amount > policy_config.max_automated_amount:
        return False, f"Guardrail Violated: Amount exceeds automated financial limit (₹{policy_config.max_automated_amount:,.0f}).", {}
    if current_retry_count >= policy_config.max_retries_per_transaction:
        return False, f"Guardrail Violated: Exceeded maximum allowed retries ({policy_config.max_retries_per_transaction}).", {}

    # 2. Cool-off period check
    now = time.time()
    if last_retry_timestamp is not None:
        elapsed = now - last_retry_timestamp
        if elapsed < policy_config.min_cooloff_seconds:
            remaining_mins = int((policy_config.min_cooloff_seconds - elapsed) / 60)
            return False, f"Guardrail Violated: Cool-off period active ({remaining_mins} mins remaining).", {}

    # 3. Discount cap & eligibility check
    sanitized_discount = max(0.0, min(requested_discount_pct, policy_config.max_discount_percent))
    if amount < policy_config.min_amount_for_discount and sanitized_discount > 0:
        sanitized_discount = 0.0

    sanitized_params = {
        "transaction_id": transaction_id,
        "allowed_retry_count": current_retry_count + 1,
        "approved_discount_pct": round(sanitized_discount, 2),
        "discount_amount": round((amount * sanitized_discount) / 100.0, 2),
        "final_payable_amount": round(amount - (amount * sanitized_discount) / 100.0, 2),
        "guardrail_status": "APPROVED"
    }

    return True, "All guardrails passed successfully.", sanitized_params


def validate_execution_scope(transaction: Dict[str, Any], action: str) -> Tuple[bool, str]:
    """Apply certification, permission, data-scope, and contact controls to one action."""
    if transaction.get("certification_status", "CERTIFIED") != "CERTIFIED":
        return False, "Execution blocked: agent is not CERTIFIED."

    policy = transaction.get("agent_policy", {})
    allowed_actions = policy.get("allowed_actions")
    if allowed_actions is not None and action not in set(allowed_actions):
        return False, f"Execution blocked: action '{action}' is outside the certified action scope."
    if action in set(policy.get("blocked_actions", [])):
        return False, f"Execution blocked: action '{action}' is explicitly blocked by policy."

    requested_data = set(transaction.get("requested_data_scope", []))
    permitted_data = {"id", "amount", "bank", "payment_method", "error_code", "customer_tier", "retry_count", "status"}
    if not requested_data.issubset(permitted_data):
        return False, "Execution blocked: requested data is outside the certified data scope."

    is_contact_action = "LINK" in action or "WHATSAPP" in action or "SMS" in action
    if is_contact_action and (
        int(transaction.get("customer_contact_count", 0)) >= 1
        or transaction.get("last_contact_timestamp") is not None
        and time.time() - float(transaction["last_contact_timestamp"]) < 86400
    ):
        return False, "Execution blocked: customer contact limit is active for the configured 24-hour window."
    return True, "Execution scope validated."


def validate_ai_output_schema(ai_response: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Anti-hallucination schema validator for AI strategy agent output.
    """
    required_keys = ["recommended_action", "confidence_score", "rationale", "cascaded_channels"]
    for key in required_keys:
        if key not in ai_response:
            return False, f"Invalid AI schema: missing key '{key}'"
            
    confidence = ai_response.get("confidence_score", 0.0)
    if not (0.0 <= confidence <= 1.0):
        return False, f"Invalid confidence score: {confidence}. Must be between 0.0 and 1.0"
        
    allowed_actions = [
        "SMART_RETRY_NOW",
        "SCHEDULE_SMART_RETRY",
        "SEND_WHATSAPP_PAYLINK",
        "SEND_SMS_PAYLINK",
        "OFFER_DYNAMIC_INCENTIVE",
        "SWITCH_GATEWAY_ROUTING",
        "MANUAL_HUMAN_REVIEW"
    ]
    if ai_response.get("recommended_action") not in allowed_actions:
        return False, f"Unauthorized AI action: '{ai_response.get('recommended_action')}'"

    return True, "AI schema validated."
