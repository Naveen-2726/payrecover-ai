from typing import Any, Dict, Iterable, List

from app.analytics.payment_intelligence import diagnose_payment


def detect_recovery_opportunities(transactions: Iterable[Dict[str, Any]], limit: int = 10) -> Dict[str, Any]:
    """Rank unresolved revenue by deterministic opportunity value."""
    opportunities: List[Dict[str, Any]] = []
    for transaction in transactions:
        status = transaction.get("status", "FAILED")
        amount = float(transaction.get("amount", 0.0))
        if status in {"RECOVERED", "RECOVERED_OR_LATE_AUTHORIZED", "CLOSED"}:
            continue
        diagnosis = diagnose_payment(transaction)
        probability = float(diagnosis["diagnosis"]["recovery_probability"])
        expected_value = float(diagnosis["diagnosis"]["expected_net_recovery_inr"])
        retry_exhausted = int(transaction.get("retry_count", 0)) >= 3
        priority = "HIGH" if amount >= 10000 or expected_value >= 5000 else "MEDIUM" if expected_value >= 1000 else "LOW"
        if retry_exhausted:
            priority = "HIGH"
        opportunities.append({
            "payment_id": transaction.get("id"),
            "source": transaction.get("source", "payment"),
            "amount_inr": round(amount, 2),
            "priority": priority,
            "opportunity_value_inr": round(max(0.0, expected_value), 2),
            "recovery_probability_pct": round(probability * 100, 1),
            "recommended_action": diagnosis["diagnosis"]["best_action"],
            "reason": diagnosis["diagnosis"]["why"],
            "final_state": status,
            "synthetic_context": True,
        })
    opportunities.sort(key=lambda item: (item["opportunity_value_inr"], item["amount_inr"]), reverse=True)
    return {
        "opportunities": opportunities[:limit],
        "total_opportunities": len(opportunities),
        "total_opportunity_value_inr": round(sum(item["opportunity_value_inr"] for item in opportunities), 2),
        "synthetic_context": True,
    }
