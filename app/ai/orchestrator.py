import time
from typing import Dict, Any, List
from app.core.state_machine import payment_state_machine, PaymentState
from app.core.health_engine import payment_health_engine
from app.core.error_semantics import error_semantic_engine, evaluate_confidence_abstention
from app.ai.optimizer import action_optimizer
from app.ml.engine import ml_engine
from app.safety.guardrails import validate_recovery_guardrails, validate_execution_scope
from app.ai.health_monitor import agent_health_monitor
from app.audit.ledger import ledger_instance
from app.ai.observability import agent_observability

class AIRecoveryOrchestrator:
    """
    Central AI Recovery Orchestrator incorporating:
    - Razorpay Error Semantics
    - Payment Network Health & Downtime-Aware Routing
    - Late Authorization Safety Protection
    - Multi-Action Expected Net Value Optimization
    - Confidence Abstention Tiering
    - Structured Explanation & Decision Graph
    """

    def orchestrate_recovery(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        started_at = time.perf_counter()
        tx_id = transaction.get("id", f"tx_{int(time.time())}")
        amount = float(transaction.get("amount", 0.0))
        if transaction.get("certification_status", "CERTIFIED") != "CERTIFIED":
            reason = "Execution blocked: agent is not CERTIFIED."
            ledger_instance.append_event("AGENT_ACTION_BLOCKED_UNCERTIFIED", tx_id, {"reason": reason})
            result = self._blocked_result(tx_id, "AGENT_NOT_CERTIFIED", reason)
            agent_observability.record_decision(result, (time.perf_counter() - started_at) * 1000)
            return result
        if not agent_health_monitor.is_active():
            ledger_instance.append_event(
                event_type="AGENT_ACTION_BLOCKED_KILL_SWITCH",
                transaction_id=tx_id,
                details={"state": agent_health_monitor.state, "reason": agent_health_monitor.reason},
            )
            result = self._blocked_result(tx_id, "AGENT_PAUSED", agent_health_monitor.reason, health_monitor=True)
            agent_observability.record_decision(result, (time.perf_counter() - started_at) * 1000)
            return result

        error_code = transaction.get("error_code", "BAD_REQUEST_PAYMENT_TIMED_OUT")
        bank = transaction.get("bank", "HDFC").upper()
        payment_method = transaction.get("payment_method", "upi_intent").lower()
        retry_count = int(transaction.get("retry_count", 0))
        current_state = transaction.get("status", PaymentState.FAILED)
        last_retry = transaction.get("last_retry_timestamp", None)

        # Step 1: Error Semantics Classification
        semantics = error_semantic_engine.analyze_error_semantics(
            error_code=error_code,
            error_source=transaction.get("error_source", "bank"),
            error_step=transaction.get("error_step", "payment_authentication")
        )
        category = semantics["category"]

        # Step 2: Payment Network Health Check (Downtime-Aware)
        health_info = payment_health_engine.evaluate_health(bank, payment_method)

        # Step 3: Late Authorization Protection Check
        late_auth_active = False
        late_auth_msg = ""
        if category == "POTENTIALLY_LATE_AUTHORIZABLE" or error_code == "BAD_REQUEST_PAYMENT_TIMED_OUT":
            late_auth_active = True
            late_auth_msg = f"Late Authorization Protection Active: Payment {tx_id} timed out. Monitoring for incoming payment.captured webhook before executing retry."

        # Step 4: ML Propensity Engine
        ml_res = ml_engine.predict_recovery_propensity(transaction)
        p_base = ml_res["p_recovery"]
        opt_hour = ml_res["optimal_retry_hour"]
        rec_discount = ml_res["recommended_discount_pct"]

        # Step 5: Guardrail Check
        is_allowed, g_reason, sanitized = validate_recovery_guardrails(
            transaction_id=tx_id,
            amount=amount,
            current_retry_count=retry_count,
            requested_discount_pct=rec_discount,
            last_retry_timestamp=last_retry
        )
        approved_discount = sanitized.get("approved_discount_pct", 0.0) if is_allowed else 0.0

        # Step 6: Multi-Action Expected Net Value Optimization
        winning_action, candidate_matrix = action_optimizer.evaluate_candidate_actions(
            base_p_recovery=p_base,
            amount=amount,
            failure_category=category,
            discount_pct=approved_discount
        )

        selected_action = winning_action["action"]

        # Adjust action based on Network Health & Late Auth Protection
        if not health_info["allow_same_channel_retry"] and selected_action in ["SMART_RETRY", "SCHEDULE_RETRY"]:
            selected_action = "SWITCH_PAYMENT_METHOD"
            winning_action["action"] = "SWITCH_PAYMENT_METHOD"

        if late_auth_active and retry_count == 0:
            selected_action = "SCHEDULE_RETRY"  # Delay retry to wait for potential late auth

        scope_allowed, scope_reason = validate_execution_scope(transaction, selected_action)
        if not scope_allowed:
            is_allowed = False
            g_reason = scope_reason
        if not is_allowed:
            ledger_instance.append_event(
                "RECOVERY_ACTION_BLOCKED_GUARDRAIL",
                tx_id,
                {"action": selected_action, "reason": g_reason, "amount": amount},
            )

        # Step 7: Confidence & Abstention Evaluation
        conf_tier, conf_msg, is_abstain = evaluate_confidence_abstention(winning_action["probability"])
        requires_human = False

        if is_abstain or not is_allowed or category == "PERMANENT_PAYMENT_FAILURE" or retry_count >= 3:
            selected_action = "HUMAN_ESCALATION" if not is_abstain else "NO_ACTION"
            requires_human = True

        # Step 8: State Machine Transition Evaluation
        if late_auth_active and current_state == PaymentState.FAILED:
            _, target_state, state_msg = payment_state_machine.transition(
                current_state=current_state,
                target_state=PaymentState.POTENTIALLY_LATE_AUTHORIZABLE,
                transaction_id=tx_id,
                event_reason=late_auth_msg
            )
        elif requires_human:
            _, target_state, state_msg = payment_state_machine.transition(
                current_state=current_state,
                target_state=PaymentState.ESCALATED,
                transaction_id=tx_id,
                event_reason="Human escalation required"
            )
        else:
            _, target_state, state_msg = payment_state_machine.transition(
                current_state=current_state,
                target_state=PaymentState.RECOVERY_PENDING,
                transaction_id=tx_id,
                event_reason="Automated recovery strategy scheduled"
            )

        # Step 9: Structured 4-Why Explanation
        explanation = {
            "why_this_payment": f"₹{amount:,.2f} transaction at {bank} flagged due to {category} ({error_code}).",
            "why_this_action": f"Selected '{selected_action}' via Expected Net Value optimization (EV: ₹{winning_action['expected_value_score']}).",
            "why_now": f"Issuing bank channel {bank} {payment_method} is currently {health_info['status']}. Optimal timing: {opt_hour:02d}:00 HRS.",
            "why_not_others": f"Same-channel retries offer lower expected recovery value under current network health."
        }

        # Step 10: Visual Recovery Decision Graph Nodes
        decision_graph = [
            {"step": "PAYMENT_FAILURE", "status": "COMPLETED", "detail": f"Failed: {error_code}"},
            {"step": "ERROR_SEMANTICS", "status": "COMPLETED", "detail": f"Category: {category}"},
            {"step": "LATE_AUTH_CHECK", "status": "TRIGGERED" if late_auth_active else "PASSED", "detail": late_auth_msg or "No late auth risk"},
            {"step": "NETWORK_HEALTH", "status": "COMPLETED", "detail": f"{bank} Status: {health_info['status']} ({health_info['success_rate_pct']}%)"},
            {"step": "ML_PREDICTION", "status": "COMPLETED", "detail": f"Propensity P(rec): {round(p_base*100,1)}%"},
            {"step": "EV_OPTIMIZATION", "status": "COMPLETED", "detail": f"Selected: {selected_action} (EV: ₹{winning_action['expected_value_score']})"},
            {"step": "GUARDRAIL_CHECK", "status": "APPROVED" if is_allowed else "BLOCKED", "detail": g_reason},
            {"step": "STATE_MACHINE", "status": "COMPLETED", "detail": f"State: {target_state}"}
        ]

        result = {
            "payment_id": tx_id,
            "current_state": target_state,
            "failure_category": category,
            "failure_description": semantics["description"],
            "late_authorization_protected": late_auth_active,
            "late_authorization_message": late_auth_msg,
            "network_health": health_info,
            "recovery_probability": p_base,
            "recovery_probability_pct": f"{round(p_base * 100, 1)}%",
            "revenue_risk": "HIGH" if (amount > 5000 or p_base < 0.4) else ("MEDIUM" if p_base < 0.7 else "LOW"),
            "recommended_action": selected_action,
            "recommended_time": f"{opt_hour:02d}:00 HRS",
            "expected_recovery_value": winning_action["expected_value_score"],
            "confidence_tier": conf_tier,
            "confidence_score": winning_action["probability"],
            "confidence_message": conf_msg,
            "is_abstain": is_abstain,
            "explanation": explanation,
            "feature_contributions": self._generate_feature_contributions(bank, error_code, category, p_base, amount),
            "action_matrix": candidate_matrix,
            "decision_graph": decision_graph,
            "requires_human_approval": requires_human,
            "guardrail_result": {
                "status": "APPROVED" if is_allowed else "BLOCKED",
                "reason": g_reason,
                "approved_discount_pct": approved_discount,
                "allowed_retry_count": sanitized.get("allowed_retry_count", retry_count + 1)
            },
            "agent_health": agent_health_monitor.status(),
        }
        agent_observability.record_decision(result, (time.perf_counter() - started_at) * 1000)
        return result

    def _blocked_result(self, tx_id: str, category: str, reason: str, health_monitor: bool = False) -> Dict[str, Any]:
        event_type = "AGENT_ACTION_BLOCKED_KILL_SWITCH" if health_monitor else "AGENT_ACTION_BLOCKED_UNCERTIFIED"
        if health_monitor:
            ledger_instance.append_event(event_type, tx_id, {"state": agent_health_monitor.state, "reason": reason})
        return {
            "payment_id": tx_id,
            "current_state": PaymentState.ESCALATED,
            "failure_category": category,
            "failure_description": reason,
            "recommended_action": "NO_ACTION",
            "expected_recovery_value": 0.0,
            "recovery_probability": 0.0,
            "confidence_score": 0.0,
            "is_abstain": True,
            "requires_human_approval": True,
            "late_authorization_protected": False,
            "late_authorization_message": reason,
            "agent_health": agent_health_monitor.status(),
            "guardrail_result": {"status": "BLOCKED", "reason": reason},
            "decision_graph": [{"step": "GOVERNANCE_CHECK", "status": "BLOCKED", "detail": reason}],
        }

    def _generate_feature_contributions(
        self, bank: str, error_code: str, category: str, p_base: float, amount: float
    ) -> List[Dict[str, Any]]:
        factors = []
        if bank in ["HDFC", "ICICI"]:
            factors.append({"factor": f"High Issuing Bank Uptime ({bank})", "impact": "POSITIVE", "weight": "+22%"})
        else:
            factors.append({"factor": f"Moderate Bank Network Latency ({bank})", "impact": "NEUTRAL", "weight": "+5%"})

        if category == "POTENTIALLY_LATE_AUTHORIZABLE":
            factors.append({"factor": "Transient Bank Timeout Signal (Late Auth Risk)", "impact": "POSITIVE", "weight": "+28%"})
        elif category == "CUSTOMER_ACTION_REQUIRED":
            factors.append({"factor": "Account Balance Friction Signal", "impact": "NEGATIVE", "weight": "-18%"})
        elif category == "PERMANENT_PAYMENT_FAILURE":
            factors.append({"factor": "Permanent Decline Signal", "impact": "CRITICAL_NEGATIVE", "weight": "-45%"})

        if amount > 5000:
            factors.append({"factor": "High Basket Size Recovery Motivation", "impact": "POSITIVE", "weight": "+12%"})

        return factors

recovery_orchestrator = AIRecoveryOrchestrator()
