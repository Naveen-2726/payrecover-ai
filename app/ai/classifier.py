from typing import Dict, Any, Tuple

class FailureClassifier:
    """
    Intelligent payment failure categorization engine mapping Razorpay & bank failure codes
    to deterministic operational recovery paths.
    """
    
    TEMPORARY_CODES = {
        "BAD_REQUEST_PAYMENT_TIMED_OUT": "Bank gateway timeout during authentication.",
        "GATEWAY_ERROR": "Temporary gateway unavailable or payment network drop.",
        "NETWORK_DROP": "Intermittent bank switch drop during 3DS redirect.",
        "BANK_UNAVAILABLE": "Bank CBS maintenance window active."
    }

    CUSTOMER_ACTION_CODES = {
        "CUSTOMER_INSUFFICIENT_FUNDS": "Customer account balance below order amount.",
        "AUTHENTICATION_FAILED": "3DS / OTP authentication failed by customer.",
        "OTP_TIMEOUT": "Customer did not enter OTP within valid timeframe.",
        "MANDATE_EXECUTION_FAILED": "Auto-debit mandate failed due to insufficient funds or customer revoke."
    }

    PERMANENT_CODES = {
        "INVALID_CARD": "Card number or CVV invalid.",
        "ACCOUNT_BLOCKED": "Customer bank account frozen or blocked by issuing bank.",
        "EXPIRED_CARD": "Payment card expired.",
        "PERMANENT_DECLINE": "Transaction permanently declined by issuer risk engine."
    }

    def classify(self, error_code: str) -> Tuple[str, str, str]:
        """
        Returns (category, description, recommended_strategy)
        Category is one of: 'TEMPORARY', 'CUSTOMER_ACTION_REQUIRED', 'PERMANENT', 'UNKNOWN'
        """
        code = (error_code or "").upper().strip()

        if code in self.TEMPORARY_CODES:
            return (
                "TEMPORARY",
                self.TEMPORARY_CODES[code],
                "SMART_RETRY: Schedule automated gateway retry at optimal bank uptime window."
            )
        elif code in self.CUSTOMER_ACTION_CODES:
            return (
                "CUSTOMER_ACTION_REQUIRED",
                self.CUSTOMER_ACTION_CODES[code],
                "CUSTOMER_ENGAGEMENT: Send 1-click PayLink or offer dynamic incentive via WhatsApp/SMS."
            )
        elif code in self.PERMANENT_CODES:
            return (
                "PERMANENT",
                self.PERMANENT_CODES[code],
                "STOP_AUTOMATION: Permanent decline detected. Prompt customer for alternate payment method."
            )
        else:
            return (
                "UNKNOWN",
                f"Unrecognized error code: '{error_code}'.",
                "HUMAN_REVIEW: Flag for manual merchant escalation."
            )

failure_classifier = FailureClassifier()
