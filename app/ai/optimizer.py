from typing import Dict, Any, List, Tuple

class ExpectedValueOptimizer:
    """
    Evaluates candidate recovery actions using Expected Net Recovery Value (EV):
    EV = P_recovery(action) * (Amount - IncentiveCost) - ActionCost - ContactCost
    """
    
    ACTION_SPECS = {
        "SMART_RETRY": {"action_cost": 2.0, "contact_cost": 0.0, "p_modifier": 1.0},
        "SCHEDULE_RETRY": {"action_cost": 1.0, "contact_cost": 0.0, "p_modifier": 0.95},
        "WHATSAPP_PAYMENT_LINK": {"action_cost": 3.0, "contact_cost": 0.5, "p_modifier": 0.90},
        "PAYMENT_LINK": {"action_cost": 4.0, "contact_cost": 1.0, "p_modifier": 0.85},
        "UPI_INTENT": {"action_cost": 2.5, "contact_cost": 0.0, "p_modifier": 0.88},
        "HUMAN_ESCALATION": {"action_cost": 50.0, "contact_cost": 0.0, "p_modifier": 0.70},
        "NO_ACTION": {"action_cost": 0.0, "contact_cost": 0.0, "p_modifier": 0.0}
    }

    def evaluate_candidate_actions(
        self,
        base_p_recovery: float,
        amount: float,
        failure_category: str,
        discount_pct: float = 0.0
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        
        candidates = []
        incentive_cost = (amount * discount_pct) / 100.0
        net_collectable_amount = amount - incentive_cost

        for action_name, spec in self.ACTION_SPECS.items():
            if action_name == "NO_ACTION":
                p_act = 0.0
            elif failure_category == "PERMANENT" and action_name not in ["HUMAN_ESCALATION", "NO_ACTION"]:
                p_act = 0.05  # Permanent failure unlikely to recover via retries
            elif failure_category == "CUSTOMER_ACTION_REQUIRED" and action_name in ["SMART_RETRY", "SCHEDULE_RETRY"]:
                p_act = base_p_recovery * 0.4  # Retrying insufficient funds blindly won't work
            elif failure_category == "CUSTOMER_ACTION_REQUIRED" and action_name in ["WHATSAPP_PAYMENT_LINK", "PAYMENT_LINK"]:
                p_act = min(0.95, base_p_recovery * 1.3)  # High boost for customer PayLink on low balance
            elif failure_category == "TEMPORARY" and action_name in ["SMART_RETRY", "SCHEDULE_RETRY"]:
                p_act = min(0.98, base_p_recovery * 1.25)
            else:
                p_act = min(0.95, max(0.05, base_p_recovery * spec["p_modifier"]))

            action_cost = spec["action_cost"]
            contact_cost = spec["contact_cost"]

            expected_gross = p_act * net_collectable_amount
            expected_net_value = expected_gross - action_cost - contact_cost - (incentive_cost * p_act)

            candidates.append({
                "action": action_name,
                "probability": round(p_act, 4),
                "probability_pct": f"{round(p_act * 100, 1)}%",
                "expected_recovery": round(expected_gross, 2),
                "action_cost": action_cost,
                "incentive_cost": round(incentive_cost * p_act, 2),
                "contact_cost": contact_cost,
                "expected_value_score": round(expected_net_value, 2)
            })

        # Sort candidates by highest Expected Value Score
        candidates.sort(key=lambda x: x["expected_value_score"], reverse=True)
        winner = candidates[0]

        # Construct rationale explaining why winner won
        runner_up = candidates[1] if len(candidates) > 1 else winner
        diff = round(winner["expected_value_score"] - runner_up["expected_value_score"], 2)
        
        reason = (
            f"Action '{winner['action']}' selected with highest Expected Net Recovery Value (₹{winner['expected_value_score']}). "
            f"Outperformed next best alternative '{runner_up['action']}' (₹{runner_up['expected_value_score']}) by +₹{diff}."
        )

        return winner, candidates

action_optimizer = ExpectedValueOptimizer()
