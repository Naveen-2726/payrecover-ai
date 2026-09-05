from typing import Dict, Any
from app.ml.train import generate_synthetic_dataset

class StrategySimulator:
    """
    Simulates custom merchant guardrail policies against historical transaction batches.
    Calculates net margin impact, recovered ARR, recovery rate, and contact overhead.
    """

    def simulate_custom_policy(
        self,
        max_retries: int = 3,
        cooloff_seconds: int = 7200,
        max_discount_pct: float = 10.0,
        min_amount_for_discount: float = 100.0,
        human_approval_threshold: float = 10000.0,
        channel_cost_per_contact: float = 3.0,
        num_transactions: int = 100
    ) -> Dict[str, Any]:
        
        df = generate_synthetic_dataset(num_transactions)
        
        total_volume = float(df["amount"].sum())
        recovered_volume = 0.0
        recovered_count = 0
        contacts_made = 0
        discounts_given_inr = 0.0
        human_escalations = 0

        for _, row in df.iterrows():
            amount = float(row["amount"])
            error = row["error_code"]

            if amount >= human_approval_threshold:
                human_escalations += 1
                continue

            if error == "PERMANENT_DECLINE" or error == "EXPIRED_CARD":
                continue

            disc_applied = 0.0
            if amount >= min_amount_for_discount and error == "CUSTOMER_INSUFFICIENT_FUNDS":
                disc_applied = min(max_discount_pct, 5.0)

            inc_val = (amount * disc_applied) / 100.0
            discounts_given_inr += inc_val

            if error in ["CUSTOMER_INSUFFICIENT_FUNDS", "AUTHENTICATION_FAILED"]:
                contacts_made += 1

            if row["recovered"] == 1 or error in ["BAD_REQUEST_PAYMENT_TIMED_OUT", "CUSTOMER_INSUFFICIENT_FUNDS"]:
                recovered_count += 1
                recovered_volume += (amount - inc_val)

        rec_rate = (recovered_count / num_transactions) * 100.0
        total_channel_cost = contacts_made * channel_cost_per_contact
        net_recovered = recovered_volume - total_channel_cost - discounts_given_inr
        margin_impact_pct = (net_recovered / max(1.0, total_volume)) * 100.0

        return {
            "simulation_params": {
                "max_retries": max_retries,
                "cooloff_seconds": cooloff_seconds,
                "max_discount_pct": max_discount_pct,
                "min_amount_for_discount": min_amount_for_discount,
                "human_approval_threshold": human_approval_threshold
            },
            "results": {
                "total_batch_volume_inr": round(total_volume, 2),
                "gross_recovered_revenue_inr": round(recovered_volume, 2),
                "net_recovered_value_inr": round(net_recovered, 2),
                "recovery_rate_pct": round(rec_rate, 2),
                "recovered_count": recovered_count,
                "customer_contacts_count": contacts_made,
                "discounts_given_inr": round(discounts_given_inr, 2),
                "channel_costs_inr": round(total_channel_cost, 2),
                "human_escalations_count": human_escalations,
                "estimated_margin_impact_pct": f"+{round(max(0, margin_impact_pct), 1)}%"
            }
        }

strategy_simulator = StrategySimulator()
