from copy import deepcopy
from typing import Any, Dict, Optional

from app.ai.orchestrator import recovery_orchestrator
from app.audit.ledger import ledger_instance
from app.core.state_machine import PaymentState


def replay_recovery_decision(transaction: Dict[str, Any], alternative_action: Optional[str] = None) -> Dict[str, Any]:
    """Replay diagnosis/decision logic and compare a candidate alternative."""
    replay_input = deepcopy(transaction)
    replay_input["id"] = f"replay_{transaction.get('id', 'unknown')}"
    replay_input["status"] = PaymentState.FAILED
    replay_input["retry_count"] = int(transaction.get("retry_count", 0))
    decision = recovery_orchestrator.orchestrate_recovery(replay_input)
    candidates = decision.get("action_matrix", [])
    actual_action = transaction.get("orchestration", {}).get("recommended_action", decision.get("recommended_action"))
    selected_alternative = alternative_action
    if selected_alternative is None:
        for candidate in candidates:
            if candidate.get("action") != actual_action:
                selected_alternative = candidate.get("action")
                break
    alternative = next((candidate for candidate in candidates if candidate.get("action") == selected_alternative), None)
    actual_recovered = float(transaction.get("recovered_amount", 0.0))
    alternative_expected = float(alternative.get("expected_recovery", 0.0)) if alternative else 0.0
    result = {
        "payment_id": transaction.get("id"),
        "timeline": decision.get("decision_graph", []),
        "actual": {
            "action": actual_action,
            "recovered_amount_inr": actual_recovered,
            "final_state": transaction.get("status"),
        },
        "alternative": {
            "action": selected_alternative,
            "expected_recovery_inr": round(alternative_expected, 2),
            "estimate_only": True,
        },
        "difference_inr": round(actual_recovered - alternative_expected, 2),
        "audit_history": ledger_instance.get_transaction_history(str(transaction.get("id"))),
        "synthetic_replay": True,
    }
    ledger_instance.append_event(
        "RECOVERY_DECISION_REPLAYED",
        str(transaction.get("id")),
        {"actual_action": actual_action, "alternative_action": selected_alternative, "estimate_only": True},
    )
    return result
