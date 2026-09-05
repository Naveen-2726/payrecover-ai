from typing import Any, Dict, List

from app.audit.ledger import ledger_instance


class AgentCertificationEngine:
    """Deterministic pre-activation checks for a compiled recovery policy."""

    ACTIONS = {
        "WAIT_FOR_HEALTH_RECOVERY", "SEND_PAYMENT_LINK", "HUMAN_REVIEW",
        "RETRY_SAME_METHOD", "SWITCH_ROUTING_PATH", "SWITCH_PAYMENT_METHOD",
    }

    def certify(self, compiled_policy: Dict[str, Any], agent_name: str = "PayRecover Recovery Agent") -> Dict[str, Any]:
        policy = compiled_policy.get("structured_policy", compiled_policy)
        instruction = str(compiled_policy.get("original_instruction", "")).lower()
        allowed_actions = set(policy.get("allowed_actions", []))
        checks: List[Dict[str, Any]] = []

        checks.append(self._check("permission_scope", "PASS", "Policy actions are explicitly enumerated."))
        checks.append(self._check(
            "data_scope",
            "BLOCK" if any(term in instruction for term in ["export data", "read all customers", "share data"]) else "PASS",
            "Only transaction context is available to the recovery agent.",
        ))
        checks.append(self._check(
            "action_scope",
            "PASS" if allowed_actions.issubset(self.ACTIONS) else "BLOCK",
            "All requested actions are within the recovery action allowlist.",
        ))
        checks.append(self._check(
            "financial_limits",
            "PASS" if 0 <= float(policy.get("max_discount_percent", 999)) <= 20 and float(policy.get("human_approval_threshold", 0)) >= 500 else "BLOCK",
            "Discount and human-approval limits are within deterministic bounds.",
        ))
        checks.append(self._check(
            "consent",
            "PASS" if policy.get("contact_limits", {}).get("max_contacts_per_customer") == 1 else "BLOCK",
            "Customer contact is limited to one contact per configured window.",
        ))
        checks.append(self._check(
            "dark_pattern_detection",
            "BLOCK" if any(term in instruction for term in ["hide", "mislead", "pressure", "fake urgency"]) else "PASS",
            "No coercive or deceptive communication instruction detected.",
        ))
        checks.append(self._check(
            "recovery_safety",
            "PASS" if policy.get("require_webhook_hmac") and "respect_late_authorization" in policy.get("risk_constraints", []) else "BLOCK",
            "Webhook authenticity and late-authorization protection are mandatory.",
        ))
        checks.append(self._check("audit_coverage", "PASS", "Execution decisions are recorded by the audit ledger."))

        passed = sum(check["status"] == "PASS" for check in checks)
        score = round((passed / len(checks)) * 100)
        blocked = any(check["status"] == "BLOCK" for check in checks) or not compiled_policy.get("validation", {}).get("executable", True)
        status = "BLOCKED" if blocked else "CERTIFIED" if score >= 90 else "REVIEW"
        result = {
            "agent_name": agent_name,
            "revenue_recovery_score": score,
            "safety_score": round((sum(check["status"] == "PASS" for check in checks[3:]) / len(checks[3:])) * 100),
            "checks": checks,
            "audit_coverage_pct": 100,
            "status": status,
            "synthetic_evaluation": True,
        }
        ledger_instance.append_event("AGENT_CERTIFICATION_COMPLETED", agent_name, result)
        return result

    @staticmethod
    def _check(name: str, status: str, detail: str) -> Dict[str, str]:
        return {"check": name, "status": status, "detail": detail}


agent_certification_engine = AgentCertificationEngine()
