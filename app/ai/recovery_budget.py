from typing import Any, Dict

from app.audit.ledger import ledger_instance


class RecoveryBudget:
    """In-memory synthetic merchant budget for autonomous recovery actions."""

    def __init__(self, daily_limit_inr: float = 5000.0):
        self.daily_limit_inr = float(daily_limit_inr)
        self.used_inr = 0.0

    def authorize(self, transaction_id: str, action: str, cost_inr: float) -> Dict[str, Any]:
        cost = max(0.0, float(cost_inr))
        remaining = self.daily_limit_inr - self.used_inr
        allowed = cost <= remaining
        result = {
            "allowed": allowed,
            "action": action,
            "cost_inr": round(cost, 2),
            "daily_limit_inr": round(self.daily_limit_inr, 2),
            "used_inr": round(self.used_inr, 2),
            "remaining_inr": round(max(0.0, remaining), 2),
            "reason": "Budget available." if allowed else "Autonomous recovery budget exhausted.",
        }
        if allowed:
            self.used_inr += cost
            result["used_inr"] = round(self.used_inr, 2)
            result["remaining_inr"] = round(self.daily_limit_inr - self.used_inr, 2)
        else:
            ledger_instance.append_event("RECOVERY_BUDGET_BLOCKED", transaction_id, result)
        return result

    def status(self) -> Dict[str, Any]:
        return {
            "daily_limit_inr": round(self.daily_limit_inr, 2),
            "used_inr": round(self.used_inr, 2),
            "remaining_inr": round(max(0.0, self.daily_limit_inr - self.used_inr), 2),
            "autonomous_actions_paused": self.used_inr >= self.daily_limit_inr,
            "synthetic_demo_data": True,
        }

    def reset(self) -> Dict[str, Any]:
        self.used_inr = 0.0
        ledger_instance.append_event("RECOVERY_BUDGET_RESET", "SYSTEM", self.status())
        return self.status()


recovery_budget = RecoveryBudget()
