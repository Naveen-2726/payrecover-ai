from typing import Any, Dict, Optional

from app.audit.ledger import ledger_instance


class AgentHealthMonitor:
    def __init__(self):
        self.state = "ACTIVE"
        self.certification_status = "CERTIFIED"
        self.reason = "Agent initialized and awaiting evaluation."
        self.last_evaluation: Optional[Dict[str, Any]] = None

    def record_evaluation(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        self.last_evaluation = evaluation
        if evaluation.get("unsafe_actions", 0) > 0:
            self.pause("Unsafe action detected during sandbox evaluation.")
        elif evaluation.get("certification", {}).get("status") == "BLOCKED":
            self.pause("Certification blocked agent activation.")
        elif evaluation.get("economic_score_pct", 0) < 50:
            self.state = "DEGRADED"
            self.reason = "Economic performance below the monitoring threshold."
        else:
            self.state = "ACTIVE"
            self.reason = "Sandbox evaluation passed monitoring thresholds."
        return self.status()

    def pause(self, reason: str) -> Dict[str, Any]:
        self.state = "PAUSED"
        self.reason = reason
        ledger_instance.append_event("AGENT_KILL_SWITCH_PAUSED", "PayRecover Recovery Agent", {"reason": reason})
        return self.status()

    def set_certification_status(self, status: str, reason: str = "") -> Dict[str, Any]:
        self.certification_status = status.upper()
        if self.certification_status != "CERTIFIED":
            self.state = "PAUSED"
            self.reason = reason or "Agent certification is not valid for execution."
            ledger_instance.append_event(
                "AGENT_CERTIFICATION_BLOCKED",
                "PayRecover Recovery Agent",
                {"status": self.certification_status, "reason": self.reason},
            )
        return self.status()

    def resume(self, reason: str = "Merchant resumed agent after review.") -> Dict[str, Any]:
        if self.certification_status != "CERTIFIED":
            self.reason = "Cannot resume an uncertified agent."
            ledger_instance.append_event("AGENT_RESUME_BLOCKED_UNCERTIFIED", "PayRecover Recovery Agent", {"reason": self.reason})
            return self.status()
        self.state = "ACTIVE"
        self.reason = reason
        ledger_instance.append_event("AGENT_KILL_SWITCH_RESUMED", "PayRecover Recovery Agent", {"reason": reason})
        return self.status()

    def is_active(self) -> bool:
        return self.state == "ACTIVE" and self.certification_status == "CERTIFIED"

    def status(self) -> Dict[str, Any]:
        evaluation = self.last_evaluation or {}
        return {
            "agent_name": "PayRecover Recovery Agent",
            "state": self.state,
            "certification_status": self.certification_status,
            "reason": self.reason,
            "success_rate_pct": evaluation.get("actual_recovery_rate_pct", "NOT_AVAILABLE"),
            "expected_recovery_inr": evaluation.get("expected_recovery_inr", 0.0),
            "actual_recovery_inr": evaluation.get("actual_recovery_inr", 0.0),
            "unsafe_actions": evaluation.get("unsafe_actions", 0),
            "abstention_rate_pct": round(evaluation.get("abstentions", 0) / max(1, evaluation.get("transactions_evaluated", 0)) * 100, 2),
            "policy_violations": 0,
            "synthetic_evaluation": True,
        }


agent_health_monitor = AgentHealthMonitor()
