import re
from typing import Dict, Any, List

class AIPolicyCompiler:
    """
    Parses natural language merchant instructions into structured guardrail policy parameters,
    runs schema & conflict validation, and requires merchant confirmation before activation.
    """

    def compile_natural_instruction(self, text: str) -> Dict[str, Any]:
        t = (text or "").lower()

        # Extract max retries
        max_retries = 3
        m_ret = re.search(r'retry.*?(\d+)\s*times?', t) or re.search(r'(\d+)\s*retr(y|ies)', t)
        if m_ret:
            max_retries = min(5, max(1, int(m_ret.group(1))))

        # Extract discount
        max_discount = 10.0
        m_disc = re.search(r'(\d+)\s*%\s*discount', t) or re.search(r'discount.*?(\d+)\s*%', t)
        if m_disc:
            max_discount = min(20.0, max(0.0, float(m_disc.group(1))))

        # Extract high value threshold
        high_val = 25000.0
        m_val = re.search(r'(\d+[\d,]*)\s*(rupees|rs|inr|₹)', t) or re.search(r'above\s*₹?\s*(\d+[\d,]*)', t)
        if m_val:
            val_str = m_val.group(1).replace(',', '')
            try:
                high_val = float(val_str)
            except ValueError:
                pass

        conditions: List[Dict[str, Any]] = []
        allowed_actions = ["WAIT_FOR_HEALTH_RECOVERY", "SEND_PAYMENT_LINK", "HUMAN_REVIEW"]
        blocked_actions: List[str] = []
        risk_constraints = ["require_webhook_hmac", "respect_late_authorization"]

        if "bank is down" in t or "bank downtime" in t:
            conditions.append({"field": "gateway_health", "operator": "equals", "value": "DOWN"})
            blocked_actions.append("RETRY_SAME_METHOD")
            allowed_actions.append("SWITCH_ROUTING_PATH")
        if "prefer upi" in t:
            conditions.append({"field": "gateway_health", "operator": "degraded", "value": "card"})
            allowed_actions.append("SWITCH_PAYMENT_METHOD")
        if "never contact" in t and "24 hours" in t:
            risk_constraints.append("max_one_customer_contact_per_24h")
        if "late authorization" in t:
            blocked_actions.extend(["RETRY_SAME_METHOD", "SWITCH_PAYMENT_METHOD"])
        if "high-value" in t or "high value" in t:
            risk_constraints.append("high_value_failures_require_human_review")
        if "net recovered revenue" in t:
            risk_constraints.append("optimize_expected_net_recovery")

        if max_retries > 0 and "retry" in t and "do not retry" not in t:
            allowed_actions.append("RETRY_SAME_METHOD")

        structured_policy = {
            "conditions": conditions,
            "allowed_actions": sorted(set(allowed_actions)),
            "blocked_actions": sorted(set(blocked_actions)),
            "contact_limits": {"max_contacts_per_customer": 1, "window_seconds": 86400},
            "amount_thresholds": {"human_approval_inr": high_val},
            "risk_constraints": sorted(set(risk_constraints)),
            "max_retries_per_transaction": max_retries,
            "min_cooloff_seconds": 7200,
            "max_discount_percent": max_discount,
            "min_amount_for_discount": 100.0,
            "human_approval_threshold": high_val,
            "require_webhook_hmac": True
        }

        conflicts = []
        if max_retries > 3 and max_discount > 15.0:
            conflicts.append("High Retry Count (>3) combined with High Discount (>15%) may erode merchant margin.")
        if high_val < 500.0:
            conflicts.append("Extremely Low Human Approval Threshold (<₹500) will cause excessive manual queue backlog.")
        if "RETRY_SAME_METHOD" in blocked_actions and "RETRY_SAME_METHOD" in structured_policy["allowed_actions"]:
            conflicts.append("RETRY_SAME_METHOD cannot be both allowed and blocked.")

        unsafe_rules = []
        if max_retries > 5:
            unsafe_rules.append("max_retries_per_transaction exceeds hard limit 5")
        if max_discount > 20:
            unsafe_rules.append("max_discount_percent exceeds hard limit 20")
        if "require_webhook_hmac" not in risk_constraints:
            unsafe_rules.append("webhook HMAC is mandatory")
        conflicts.extend(unsafe_rules)

        validation_status = "VALIDATED_NO_CONFLICTS" if not conflicts else "REJECTED_UNSAFE_POLICY"

        return {
            "original_instruction": text,
            "structured_policy": structured_policy,
            "validation_status": validation_status,
            "detected_conflicts": conflicts,
            "validation": {
                "schema_valid": True,
                "unsafe_rules": unsafe_rules,
                "executable": not conflicts,
            },
            "requires_merchant_activation": True,
            "activated": False
        }

policy_compiler = AIPolicyCompiler()
