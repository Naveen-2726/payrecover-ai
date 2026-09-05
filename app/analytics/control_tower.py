from typing import Any, Dict, Iterable, List


RECOVERED_STATES = {"RECOVERED", "RECOVERED_OR_LATE_AUTHORIZED"}


def _baseline_probability(transaction: Dict[str, Any]) -> float:
    """Deterministic no-AI baseline expectation for one failed transaction."""
    error_code = transaction.get("error_code", "")
    if error_code in {"EXPIRED_CARD", "PERMANENT_DECLINE"}:
        return 0.0
    if error_code in {"BAD_REQUEST_PAYMENT_TIMED_OUT", "GATEWAY_ERROR"}:
        return 0.30
    if error_code == "CUSTOMER_INSUFFICIENT_FUNDS":
        return 0.18
    return 0.24


def build_recovery_control_tower(
    transactions: Iterable[Dict[str, Any]],
    subscription_metrics: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build auditable recovery metrics from transaction-level records only."""
    records: List[Dict[str, Any]] = list(transactions)
    total_volume = sum(float(tx.get("amount", 0.0)) for tx in records)
    # The input is the failed-payment cohort; a later recovery does not erase its risk.
    failed_value = total_volume
    recovered_revenue = sum(float(tx.get("recovered_amount", 0.0)) for tx in records)
    baseline_expected = sum(
        float(tx.get("amount", 0.0)) * _baseline_probability(tx) for tx in records
    )
    attempts = sum(int(tx.get("retry_count", 0)) for tx in records)
    contacts = sum(
        1
        for tx in records
        if "LINK" in str(tx.get("orchestration", {}).get("recommended_action", ""))
        or "WHATSAPP" in str(tx.get("orchestration", {}).get("recommended_action", ""))
    )
    late_auth_exposure = sum(
        float(tx.get("amount", 0.0))
        for tx in records
        if tx.get("orchestration", {}).get("late_authorization_protected")
    )
    action_cost = sum(
        float(next(
            (
                candidate.get("action_cost", 0.0)
                for candidate in tx.get("orchestration", {}).get("action_matrix", [])
                if candidate.get("action") == tx.get("orchestration", {}).get("recommended_action")
            ),
            0.0,
        ))
        for tx in records
    )
    incremental = recovered_revenue - baseline_expected
    payment_records = [tx for tx in records if tx.get("source") != "subscription"]
    payment_recovered = sum(float(tx.get("recovered_amount", 0.0)) for tx in payment_records)
    payment_baseline = sum(
        float(tx.get("amount", 0.0)) * _baseline_probability(tx) for tx in payment_records
    )
    recovery_rate = (recovered_revenue / failed_value * 100.0) if failed_value else 0.0
    metrics = {
        "total_payment_volume_inr": round(total_volume, 2),
        "failed_payment_value_inr": round(failed_value, 2),
        "revenue_currently_at_risk_inr": round(failed_value, 2),
        "predicted_recoverable_revenue_inr": round(
            sum(float(tx.get("amount", 0.0)) * float(
                tx.get("orchestration", {}).get("recovery_probability", 0.0)
            ) for tx in records),
            2,
        ),
        "revenue_recovered_inr": round(recovered_revenue, 2),
        "recovery_rate_pct": round(recovery_rate, 2),
        "baseline_expected_recovery_inr": round(baseline_expected, 2),
        "incremental_recovered_revenue_inr": round(incremental, 2),
        "incremental_recovered_revenue_definition": "observed recovered revenue minus deterministic baseline expected recovery",
        "payment_cohort_incremental_recovered_revenue_inr": round(payment_recovered - payment_baseline, 2),
        "payment_cohort_incremental_revenue_definition": "payment-only seeded control-tower cohort; excludes subscription records",
        "recovery_cost_inr": round(action_cost, 2),
        "net_recovered_revenue_inr": round(recovered_revenue - action_cost, 2),
        "avoided_unnecessary_retry_attempts": sum(
            1 for tx in records if tx.get("orchestration", {}).get("late_authorization_protected")
        ),
        "customer_contacts_avoided": max(0, len(records) - contacts),
        "late_authorisation_exposure_inr": round(late_auth_exposure, 2),
    }
    if subscription_metrics:
        metrics["subscription_revenue_at_risk_inr"] = round(
            float(subscription_metrics.get("at_risk_revenue_inr", 0.0)), 2
        )
        metrics["subscription_recovered_revenue_inr"] = round(
            float(subscription_metrics.get("recovered_revenue_inr", 0.0)), 2
        )
        metrics["subscription_recovery_rate_pct"] = float(
            subscription_metrics.get("recovery_rate_pct", 0.0)
        )
    return {
        "record_count": len(records),
        "subscription_record_count": sum(1 for tx in records if tx.get("source") == "subscription"),
        "metrics": metrics,
    }
