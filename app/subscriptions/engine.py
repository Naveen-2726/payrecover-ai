from typing import Dict, Any, List
from app.audit.ledger import ledger_instance

class SubscriptionState:
    ACTIVE = "ACTIVE"
    PAYMENT_DUE = "PAYMENT_DUE"
    FAILED = "FAILED"
    RECOVERY_IN_PROGRESS = "RECOVERY_IN_PROGRESS"
    RECOVERED = "RECOVERED"
    HALTED = "HALTED"


class SubscriptionRecoveryEngine:
    """
    Recurring Subscription Revenue Recovery Engine modeling Razorpay Subscriptions & Invoices.
    """

    def __init__(self):
        self.subscriptions_db = {}
        self._seed_mock_subscriptions()

    def _seed_mock_subscriptions(self):
        sample_subs = [
            {
                "id": "sub_enterprise_01",
                "customer_name": "Acme SaaS Corp",
                "plan": "Enterprise ARR Tier",
                "amount": 24999.0,
                "billing_cycle": "MONTHLY",
                "status": SubscriptionState.RECOVERED,
                "dunning_attempts": 2,
                "timeline": [
                    {"day": "Day 0", "event": "Subscription Charge Failed (UPI Autopay Timeout)", "status": "FAILED"},
                    {"day": "Day 1", "event": "AI Smart Gateway Retry (Post HDFC Window)", "status": "RETRY_ATTEMPTED"},
                    {"day": "Day 2", "event": "Alternate Payment Method Swap (Credit Card)", "status": "METHOD_SWAPPED"},
                    {"day": "Day 3", "event": "Subscription Charge Recovered (₹24,999)", "status": "RECOVERED"}
                ]
            },
            {
                "id": "sub_growth_02",
                "customer_name": "TechStart Media",
                "plan": "Growth Pro Tier",
                "amount": 4999.0,
                "billing_cycle": "MONTHLY",
                "status": SubscriptionState.RECOVERY_IN_PROGRESS,
                "dunning_attempts": 1,
                "timeline": [
                    {"day": "Day 0", "event": "Auto-debit Mandate Failed (Insufficient Funds)", "status": "FAILED"},
                    {"day": "Day 1", "event": "WhatsApp 1-Click Incentive PayLink Sent (5% Off)", "status": "LINK_SENT"},
                    {"day": "Day 2", "event": "Awaiting Customer Authorization", "status": "PENDING"}
                ]
            },
            {
                "id": "sub_starter_03",
                "customer_name": "Retail Global",
                "plan": "Starter Monthly",
                "amount": 1499.0,
                "billing_cycle": "MONTHLY",
                "status": SubscriptionState.HALTED,
                "dunning_attempts": 3,
                "timeline": [
                    {"day": "Day 0", "event": "Charge Failed (Card Expired)", "status": "FAILED"},
                    {"day": "Day 1", "event": "Automated Retry Failed", "status": "FAILED"},
                    {"day": "Day 2", "event": "SMS Reminder Ignored", "status": "FAILED"},
                    {"day": "Day 3", "event": "Subscription Halted (Max Retries Reached)", "status": "HALTED"}
                ]
            }
        ]
        for sub in sample_subs:
            self.subscriptions_db[sub["id"]] = sub
            for event in sub["timeline"]:
                ledger_instance.append_event(
                    event_type="SYNTHETIC_SUBSCRIPTION_EVENT",
                    transaction_id=sub["id"],
                    details={"event": event, "synthetic_demo_data": True},
                )

    def get_transaction_records(self) -> List[Dict[str, Any]]:
        """Expose subscription charges in the same shape as payment transactions."""
        records = []
        for sub in self.subscriptions_db.values():
            recovered = sub["status"] == SubscriptionState.RECOVERED
            error_code = (
                "BAD_REQUEST_PAYMENT_TIMED_OUT"
                if "Timeout" in sub["timeline"][0]["event"]
                else "CUSTOMER_INSUFFICIENT_FUNDS"
                if "Insufficient Funds" in sub["timeline"][0]["event"]
                else "EXPIRED_CARD"
            )
            action = (
                "SWITCH_PAYMENT_METHOD" if recovered and sub["id"] == "sub_enterprise_01"
                else "SEND_PAYMENT_LINK" if sub["status"] == SubscriptionState.RECOVERY_IN_PROGRESS
                else "NO_ACTION"
            )
            records.append({
                "id": sub["id"],
                "subscription_id": sub["id"],
                "source": "subscription",
                "synthetic_demo_data": True,
                "amount": float(sub["amount"]),
                "error_code": error_code,
                "status": "RECOVERED" if recovered else "RECOVERY_PENDING" if sub["status"] == SubscriptionState.RECOVERY_IN_PROGRESS else "ESCALATED",
                "recovered_amount": float(sub["amount"]) if recovered else 0.0,
                "retry_count": int(sub["dunning_attempts"]),
                "orchestration": {
                    "recommended_action": action,
                    "recovery_probability": 0.95 if recovered else 0.45 if sub["status"] == SubscriptionState.RECOVERY_IN_PROGRESS else 0.05,
                    "late_authorization_protected": False,
                    "action_matrix": [],
                },
            })
        return records

    def get_subscription_metrics(self) -> Dict[str, Any]:
        """
        Calculate metrics directly from synthetic subscription records.
        """
        records = self.get_transaction_records()
        total = len(records)
        at_risk = sum(1 for record in records if record["status"] != "RECOVERED")
        eligible = sum(1 for record in records if record["status"] == "RECOVERY_PENDING")
        recovered = sum(1 for record in records if record["status"] == "RECOVERED")
        halted = sum(1 for record in records if record["status"] == "ESCALATED")
        at_risk_revenue = sum(record["amount"] for record in records if record["status"] != "RECOVERED")
        predicted_recoverable = sum(record["amount"] * record["orchestration"]["recovery_probability"] for record in records)
        revenue_protected = sum(record["recovered_amount"] for record in records)

        return {
            "active_subscriptions": total,
            "at_risk_subscriptions": at_risk,
            "recovery_eligible": eligible,
            "recovered_subscriptions": recovered,
            "halted_subscriptions": halted,
            "revenue_protected_inr": round(revenue_protected, 2),
            "at_risk_revenue_inr": round(at_risk_revenue, 2),
            "predicted_recoverable_revenue_inr": round(predicted_recoverable, 2),
            "recovered_revenue_inr": round(revenue_protected, 2),
            "recovery_rate_pct": round((recovered / total * 100.0) if total else 0.0, 2),
            "synthetic_demo_data": True,
            "transaction_records": records,
            "sample_subscriptions": list(self.subscriptions_db.values())
        }

subscription_recovery_engine = SubscriptionRecoveryEngine()
