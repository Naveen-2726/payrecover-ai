from typing import Dict, Any, List, Tuple

class PaymentNetworkHealthEngine:
    """
    Simulated Payment Method & Issuing Bank Health Service.
    Tracks real-time success rates, recent failure spikes, and degradation status.
    """

    def __init__(self):
        # Simulated live network health matrix
        self.health_matrix = {
            "HDFC": {"upi_intent": 0.94, "netbanking": 0.58, "card": 0.91, "enach": 0.88},
            "ICICI": {"upi_intent": 0.92, "netbanking": 0.89, "card": 0.88, "enach": 0.85},
            "SBI": {"upi_intent": 0.72, "netbanking": 0.42, "card": 0.82, "enach": 0.45},
            "AXIS": {"upi_intent": 0.95, "netbanking": 0.90, "card": 0.92, "enach": 0.90},
            "KOTAK": {"upi_intent": 0.96, "netbanking": 0.91, "card": 0.94, "enach": 0.91}
        }

    def evaluate_health(self, bank: str, payment_method: str) -> Dict[str, Any]:
        b = bank.upper()
        m = payment_method.lower()
        
        bank_data = self.health_matrix.get(b, {"upi_intent": 0.90, "netbanking": 0.80, "card": 0.85, "enach": 0.80})
        sr = bank_data.get(m, 0.85)

        if sr >= 0.80:
            status = "HEALTHY"
            severity = "NONE"
            recommendation = "Standard retry permitted on same channel."
        elif sr >= 0.50:
            status = "DEGRADED"
            severity = "MEDIUM"
            recommendation = f"Channel {b} {m} is DEGRADED ({int(sr*100)}% SR). Avoid immediate same-channel retry; switch to UPI Intent or scheduled retry."
        else:
            status = "DOWN"
            severity = "CRITICAL"
            recommendation = f"Channel {b} {m} is DOWN ({int(sr*100)}% SR). Same-channel retry blocked. Switch payment method immediately or schedule post-maintenance retry."

        return {
            "bank": b,
            "payment_method": m,
            "success_rate_pct": round(sr * 100.0, 1),
            "status": status,
            "severity": severity,
            "recommendation": recommendation,
            "allow_same_channel_retry": status == "HEALTHY"
        }

    def get_all_network_health(self) -> Dict[str, Any]:
        result = {}
        for bank, methods in self.health_matrix.items():
            result[bank] = {}
            for method, sr in methods.items():
                st = "HEALTHY" if sr >= 0.80 else ("DEGRADED" if sr >= 0.50 else "DOWN")
                result[bank][method] = {"success_rate_pct": round(sr * 100.0, 1), "status": st}
        return result

payment_health_engine = PaymentNetworkHealthEngine()
