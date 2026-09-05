from typing import Dict, Any, Tuple

class PaymentErrorSemanticEngine:
    """
    Structured Payment Error Interpretation Engine mapping Razorpay error parameters
    (code, source, step, reason, description) to deterministic operational classifications.
    """

    def analyze_error_semantics(
        self,
        error_code: str,
        error_source: str = "bank",
        error_step: str = "payment_authentication",
        error_reason: str = "bad_request"
    ) -> Dict[str, Any]:
        code = (error_code or "").upper().strip()
        src = (error_source or "").lower()

        if code in ["BAD_REQUEST_PAYMENT_TIMED_OUT", "PAYMENT_TIMED_OUT", "GATEWAY_TIMEOUT"]:
            category = "POTENTIALLY_LATE_AUTHORIZABLE"
            desc = "Transaction timed out during bank authorization; may authorize late."
            late_auth_risk = "HIGH"
            allowed_strategies = ["MONITOR_LATE_AUTHORIZATION", "SCHEDULED_RETRY"]
        elif code in ["GATEWAY_ERROR", "NETWORK_DROP", "BANK_UNAVAILABLE"]:
            category = "BANK_FAILURE" if src == "bank" else "TRANSIENT_GATEWAY_FAILURE"
            desc = "Temporary bank or gateway switch failure."
            late_auth_risk = "LOW"
            allowed_strategies = ["SMART_RETRY", "SWITCH_PAYMENT_METHOD"]
        elif code in ["CUSTOMER_INSUFFICIENT_FUNDS", "INSUFFICIENT_FUNDS", "MANDATE_EXECUTION_FAILED"]:
            category = "CUSTOMER_ACTION_REQUIRED"
            desc = "Customer account balance insufficient for auto-debit or charge."
            late_auth_risk = "NONE"
            allowed_strategies = ["WHATSAPP_PAYMENT_LINK", "PAYMENT_LINK", "UPI_INTENT"]
        elif code in ["AUTHENTICATION_FAILED", "OTP_TIMEOUT", "BAD_REQUEST_OTP_FAILED"]:
            category = "CUSTOMER_ACTION_REQUIRED"
            desc = "3DS OTP authentication timed out or failed."
            late_auth_risk = "LOW"
            allowed_strategies = ["SMS_REMINDER", "WHATSAPP_PAYMENT_LINK"]
        elif code in ["EXPIRED_CARD", "INVALID_CARD", "ACCOUNT_BLOCKED", "PERMANENT_DECLINE"]:
            category = "PERMANENT_PAYMENT_FAILURE"
            desc = "Payment instrument permanently declined by issuing bank."
            late_auth_risk = "NONE"
            allowed_strategies = ["STOP_AUTOMATION", "HUMAN_ESCALATION"]
        elif code in ["INVALID_REQUEST", "BAD_REQUEST_MERCHANT_KEY_INVALID"]:
            category = "BUSINESS_CONFIGURATION_ERROR"
            desc = "Merchant API integration error or invalid payload configuration."
            late_auth_risk = "NONE"
            allowed_strategies = ["ESCALATE_INTEGRATION_ISSUE"]
        else:
            category = "UNKNOWN"
            desc = f"Unclassified error code: {code}"
            late_auth_risk = "MEDIUM"
            allowed_strategies = ["HUMAN_ESCALATION"]

        return {
            "error_code": code,
            "category": category,
            "description": desc,
            "late_authorization_risk": late_auth_risk,
            "allowed_recovery_strategies": allowed_strategies,
            "deterministic_mapping": True
        }


def evaluate_confidence_abstention(confidence_score: float) -> Tuple[str, str, bool]:
    """
    Evaluates AI decision confidence and applies Abstention principle.
    Returns (decision_tier, reason, is_abstain)
    """
    conf = round(float(confidence_score), 2)
    if conf >= 0.75:
        return "AUTOMATED_RECOVERY", f"High Confidence ({int(conf*100)}%): Automated recovery approved.", False
    elif conf >= 0.50:
        return "LIMITED_RECOVERY", f"Medium Confidence ({int(conf*100)}%): Flagged for limited retry / human review.", False
    else:
        return "ABSTAIN", f"Low Confidence ({int(conf*100)}%): AI Abstain triggered due to insufficient recovery evidence.", True

error_semantic_engine = PaymentErrorSemanticEngine()
