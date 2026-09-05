import time
from typing import Any, Dict


class AgentObservability:
    def __init__(self):
        self.metrics = {
            "decisions": 0,
            "actions": 0,
            "abstentions": 0,
            "human_escalations": 0,
            "guardrail_blocks": 0,
            "policy_violations": 0,
            "unsafe_actions": 0,
            "decision_latency_ms_total": 0.0,
        }

    def record_decision(self, result: Dict[str, Any], latency_ms: float) -> None:
        self.metrics["decisions"] += 1
        self.metrics["decision_latency_ms_total"] += max(0.0, float(latency_ms))
        if result.get("is_abstain"):
            self.metrics["abstentions"] += 1
        if result.get("requires_human_approval") or result.get("recommended_action") == "HUMAN_ESCALATION":
            self.metrics["human_escalations"] += 1
        if result.get("guardrail_result", {}).get("status") == "BLOCKED":
            self.metrics["guardrail_blocks"] += 1
        if result.get("failure_category") in {"AGENT_PAUSED", "AGENT_NOT_CERTIFIED"}:
            self.metrics["policy_violations"] += 1
        if result.get("recommended_action") not in {None, "NO_ACTION", "HUMAN_ESCALATION"} and result.get("guardrail_result", {}).get("status") == "BLOCKED":
            self.metrics["unsafe_actions"] += 1
        if result.get("recommended_action") not in {None, "NO_ACTION", "HUMAN_ESCALATION"} and result.get("guardrail_result", {}).get("status") != "BLOCKED":
            self.metrics["actions"] += 1

    def snapshot(self) -> Dict[str, Any]:
        decisions = self.metrics["decisions"]
        return {
            **self.metrics,
            "average_decision_latency_ms": round(self.metrics["decision_latency_ms_total"] / decisions, 2) if decisions else 0.0,
            "prediction_drift": "LOW",
            "policy_drift": "LOW",
            "performance_drift": "LOW",
            "synthetic_evaluation": True,
        }


agent_observability = AgentObservability()
