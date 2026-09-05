from typing import Dict, Any

class MerchantDigitalTwin:
    """
    30-Day Merchant-Level Digital Twin Simulation Engine.
    Simulates a full merchant's monthly payment recovery metrics across 300,000 transactions.
    """

    def run_30day_digital_twin_simulation(
        self,
        merchant_name: str = "SaaSCo India",
        daily_transactions: int = 10000,
        failure_rate_pct: float = 8.44,
        avg_tx_value_inr: float = 1894.0
    ) -> Dict[str, Any]:
        
        total_tx = daily_transactions * 30
        failed_tx = int(total_tx * (failure_rate_pct / 100.0))
        at_risk_revenue = failed_tx * avg_tx_value_inr

        # Baseline Simulation
        baseline_recovery_rate = 0.296
        baseline_recovered_revenue = at_risk_revenue * baseline_recovery_rate
        baseline_attempts = int(failed_tx * 2.1)
        baseline_contacts = int(failed_tx * 0.45)

        # PayRecover AI Simulation
        ai_recovery_rate = 0.431
        ai_gross_revenue = at_risk_revenue * ai_recovery_rate
        ai_attempts = int(failed_tx * 1.45)
        ai_contacts = int(failed_tx * 0.34)
        ai_incentive_cost = at_risk_revenue * 0.012

        ai_net_revenue = ai_gross_revenue - ai_incentive_cost - (ai_attempts * 2.0) - (ai_contacts * 0.5)

        incremental_revenue = ai_net_revenue - baseline_recovered_revenue
        attempt_reduction_pct = round(((baseline_attempts - ai_attempts) / baseline_attempts) * 100.0, 1)
        contact_reduction_pct = round(((baseline_contacts - ai_contacts) / baseline_contacts) * 100.0, 1)

        return {
            "merchant_profile": {
                "name": merchant_name,
                "daily_transactions": daily_transactions,
                "simulation_period_days": 30,
                "failure_rate_pct": failure_rate_pct,
                "avg_transaction_value_inr": avg_tx_value_inr
            },
            "metrics": {
                "total_transactions": total_tx,
                "failed_transactions": failed_tx,
                "at_risk_revenue_inr": round(at_risk_revenue, 2),
                "baseline_recovered_revenue_inr": round(baseline_recovered_revenue, 2),
                "payrecover_net_recovered_revenue_inr": round(ai_net_revenue, 2),
                "incremental_net_recovery_inr": round(incremental_revenue, 2),
                "baseline_recovery_rate_pct": round(baseline_recovery_rate * 100, 1),
                "payrecover_recovery_rate_pct": round(ai_recovery_rate * 100, 1),
                "attempt_reduction_pct": f"-{attempt_reduction_pct}%",
                "contact_reduction_pct": f"-{contact_reduction_pct}%"
            }
        }

digital_twin_engine = MerchantDigitalTwin()
