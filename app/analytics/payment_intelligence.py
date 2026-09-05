from typing import Any, Dict

from app.ai.optimizer import action_optimizer
from app.core.error_semantics import error_semantic_engine, evaluate_confidence_abstention
from app.core.health_engine import payment_health_engine
from app.ml.engine import ml_engine


def diagnose_payment(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Build a deterministic payment-context diagnosis without executing recovery."""
    error_code = transaction.get("error_code", "BAD_REQUEST_PAYMENT_TIMED_OUT")
    bank = str(transaction.get("bank", "HDFC")).upper()
    payment_method = str(transaction.get("payment_method", "upi_intent")).lower()
    amount = float(transaction.get("amount", 0.0))
    semantics = error_semantic_engine.analyze_error_semantics(
        error_code=error_code,
        error_source=transaction.get("error_source", "bank"),
        error_step=transaction.get("error_step", "payment_authentication"),
    )
    health = payment_health_engine.evaluate_health(bank, payment_method)
    ml_result = ml_engine.predict_recovery_propensity(transaction)
    winner, candidates = action_optimizer.evaluate_candidate_actions(
        base_p_recovery=ml_result["p_recovery"],
        amount=amount,
        failure_category=semantics["category"],
        discount_pct=0.0,
    )
    confidence_tier, confidence_message, is_abstain = evaluate_confidence_abstention(winner["probability"])
    diagnosis = "Temporary infrastructure failure" if semantics["category"] in {"BANK_FAILURE", "TRANSIENT_GATEWAY_FAILURE", "POTENTIALLY_LATE_AUTHORIZABLE"} else semantics["description"]
    best_window = f"{int(ml_result['optimal_retry_hour']):02d}:00-{(int(ml_result['optimal_retry_hour']) + 1) % 24:02d}:00"
    return {
        "payment_id": transaction.get("id"),
        "context": {
            "bank": bank,
            "payment_method": payment_method,
            "amount_inr": amount,
            "error_code": semantics["error_code"],
            "gateway_health": health,
            "customer_tier": transaction.get("customer_tier", "UNKNOWN"),
        },
        "diagnosis": {
            "why": f"{semantics['description']} Gateway/channel status: {health['status']}.",
            "what": diagnosis,
            "likely_outcome": "Recoverable" if ml_result["p_recovery"] >= 0.5 else "Low recovery likelihood",
            "recovery_probability": ml_result["p_recovery"],
            "recovery_probability_pct": f"{round(ml_result['p_recovery'] * 100, 1)}%",
            "best_window": best_window,
            "best_action": winner["action"],
            "expected_net_recovery_inr": winner["expected_value_score"],
            "confidence": confidence_tier,
            "confidence_message": confidence_message,
            "abstain": is_abstain,
        },
        "error_semantics": semantics,
        "candidate_actions": candidates,
        "synthetic_context": True,
    }
