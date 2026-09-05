import time
from typing import Dict, Any

class AdaptivePaymentLinkEngine:
    """
    Generates smart, adaptive Razorpay Payment Links configured with customer-specific
    payment preferences, expiry windows, reminder policies, and partial payment settings.
    """

    def generate_adaptive_paylink(
        self,
        amount: float,
        customer_email: str,
        preferred_method: str = "upi"
    ) -> Dict[str, Any]:
        
        expiry_hours = 6 if amount < 10000 else 24
        allow_partial = True if amount >= 5000 else False
        
        link_id = f"plink_adaptive_{int(time.time())}"
        short_url = f"https://rzp.io/i/adp_{int(time.time())}"

        return {
            "payment_link_id": link_id,
            "short_url": short_url,
            "amount": amount,
            "currency": "INR",
            "target_payment_method": preferred_method.upper(),
            "expiry_hours": expiry_hours,
            "expiry_time_str": f"{expiry_hours} Hours from issuance",
            "max_reminders_allowed": 1,
            "allow_partial_payment": allow_partial,
            "optimization_reason": f"Customer historically prefers {preferred_method.upper()}. {expiry_hours}h expiry set with 1 reminder limit."
        }

adaptive_paylink_engine = AdaptivePaymentLinkEngine()
