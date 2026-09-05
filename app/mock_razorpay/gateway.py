import hmac
import hashlib
import time
import json
import uuid
from typing import Dict, Any, Tuple
from app.safety.guardrails import policy_config

class RazorpayGatewaySimulator:
    def __init__(self, secret_key: str = policy_config.secret_key):
        self.secret_key = secret_key

    def generate_webhook_payload(
        self,
        event_type: str = "payment.failed",
        amount: float = 1299.00,
        bank: str = "HDFC",
        error_code: str = "BAD_REQUEST_PAYMENT_TIMED_OUT",
        customer_email: str = "customer@example.com",
        customer_phone: str = "+919876543210"
    ) -> Tuple[Dict[str, Any], bytes, str]:
        """
        Generate authentic Razorpay webhook event payload and compute valid HMAC signature.
        """
        payment_id = f"pay_{uuid.uuid4().hex[:12]}"
        order_id = f"order_{uuid.uuid4().hex[:12]}"
        event_id = f"evt_{uuid.uuid4().hex[:12]}"

        payload = {
            "entity": "event",
            "account_id": "acc_razorpay_buildathon",
            "event": event_type,
            "contains": ["payment"],
            "payload": {
                "payment": {
                    "entity": {
                        "id": payment_id,
                        "entity": "payment",
                        "amount": int(amount * 100),  # In paise
                        "currency": "INR",
                        "status": "failed" if event_type != "order.paid" else "captured",
                        "order_id": order_id,
                        "invoice_id": f"inv_{uuid.uuid4().hex[:8]}",
                        "method": "upi",
                        "amount_refunded": 0,
                        "refund_status": None,
                        "captured": True if event_type == "order.paid" else False,
                        "description": "Subscription Renewal - PayRecover AI",
                        "card_id": None,
                        "bank": bank,
                        "wallet": None,
                        "vpa": "user@okhdfcbank",
                        "email": customer_email,
                        "contact": customer_phone,
                        "fee": 26,
                        "tax": 4,
                        "error_code": error_code if event_type != "order.paid" else None,
                        "error_description": f"Transaction failed due to {error_code}",
                        "error_source": "bank",
                        "error_step": "payment_authentication",
                        "error_reason": error_code.lower(),
                        "created_at": int(time.time())
                    }
                }
            },
            "created_at": int(time.time()),
            "id": event_id
        }

        raw_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            raw_bytes,
            hashlib.sha256
        ).hexdigest()

        return payload, raw_bytes, signature

    def execute_payment_retry(self, payment_id: str, amount: float, discount_pct: float = 0.0, force_failure: bool = False) -> Dict[str, Any]:
        """
        Simulate payment retry against Razorpay-inspired mock gateway.
        """
        final_amount = amount * (1.0 - (discount_pct / 100.0))
        success = not force_failure
        
        return {
            "status": "CAPTURED" if success else "FAILED_GATEWAY_TIMEOUT",
            "razorpay_payment_id": f"pay_retry_{uuid.uuid4().hex[:8]}",
            "original_payment_id": payment_id,
            "recovered_amount": round(final_amount, 2) if success else 0.0,
            "discount_applied_pct": discount_pct if success else 0.0,
            "failure_reason": None if success else "Bank Gateway Timeout / Circuit Breaker Activated",
            "timestamp": time.time()
        }

razorpay_simulator = RazorpayGatewaySimulator()
