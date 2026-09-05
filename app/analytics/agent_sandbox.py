from typing import Any, Dict

from app.ai.certification import agent_certification_engine
from app.ai.orchestrator import recovery_orchestrator
from app.audit.ledger import ledger_instance
from app.ml.train import generate_synthetic_dataset


def run_agent_sandbox(num_transactions: int = 100) -> Dict[str, Any]:
    """Evaluate the existing recovery agent on one reproducible synthetic batch."""
    data = generate_synthetic_dataset(num_transactions)
    correct = 0
    unsafe = 0
    abstentions = 0
    incorrect = 0
    expected_recovery = 0.0
    actual_recovery = 0.0

    for index, row in data.iterrows():
        result = recovery_orchestrator.orchestrate_recovery({
            "id": f"sandbox_tx_{index}",
            "amount": row["amount"],
            "bank": row["bank"],
            "payment_method": row["payment_method"],
            "error_code": row["error_code"],
            "customer_tier": row["customer_tier"],
            "hour_of_day": row["hour_of_day"],
            "day_of_month": row["day_of_month"],
            "retry_count": row["retry_count"],
        })
        is_abstain = bool(result["is_abstain"] or result["requires_human_approval"])
        should_recover = bool(row["recovered"])
        took_automated_action = result["recommended_action"] not in {"NO_ACTION", "HUMAN_ESCALATION"}
        if result["guardrail_result"]["status"] == "BLOCKED" and took_automated_action:
            unsafe += 1
        if is_abstain:
            abstentions += 1
        if (took_automated_action == should_recover) or (is_abstain and not should_recover):
            correct += 1
        else:
            incorrect += 1
        expected_recovery += float(row["amount"]) * float(result["recovery_probability"])
        if should_recover and took_automated_action:
            actual_recovery += float(row["amount"])

    certification = agent_certification_engine.certify({
        "original_instruction": "Use bounded recovery actions with webhook verification and late authorization protection.",
        "structured_policy": {
            "allowed_actions": ["RETRY_SAME_METHOD", "SEND_PAYMENT_LINK", "HUMAN_REVIEW"],
            "max_discount_percent": 10,
            "human_approval_threshold": 25000,
            "contact_limits": {"max_contacts_per_customer": 1},
            "risk_constraints": ["require_webhook_hmac", "respect_late_authorization"],
            "require_webhook_hmac": True,
        },
        "validation": {"executable": True},
    })
    safety_score = round(max(0.0, 100.0 - (unsafe / max(1, num_transactions) * 100.0)), 2)
    economic_score = round(min(100.0, (actual_recovery / expected_recovery * 100.0) if expected_recovery else 0.0), 2)
    result = {
        "transactions_evaluated": num_transactions,
        "correct_decisions": correct,
        "unsafe_actions": unsafe,
        "abstentions": abstentions,
        "incorrect_actions": incorrect,
        "expected_recovery_inr": round(expected_recovery, 2),
        "actual_recovery_inr": round(actual_recovery, 2),
        "actual_recovery_rate_pct": round((actual_recovery / float(data["amount"].sum()) * 100.0) if len(data) else 0.0, 2),
        "safety_score_pct": safety_score,
        "economic_score_pct": economic_score,
        "certification": certification,
        "status": "PASS" if unsafe == 0 and certification["status"] == "CERTIFIED" else "REVIEW",
        "synthetic_evaluation": True,
    }
    ledger_instance.append_event("AGENT_SANDBOX_EVALUATED", "PayRecover Recovery Agent", result)
    return result
