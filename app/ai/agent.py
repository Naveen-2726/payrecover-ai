import time
from typing import Dict, Any
from app.ml.engine import ml_engine
from app.safety.guardrails import validate_recovery_guardrails, validate_ai_output_schema

class AIRecoveryAgent:
    def __init__(self):
        pass

    def evaluate_and_generate_plan(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate intelligent recovery plan based on payment failure context, ML propensity,
        and enforced guardrails.
        """
        tx_id = transaction.get("id", "tx_unknown")
        amount = float(transaction.get("amount", 0.0))
        error_code = transaction.get("error_code", "BAD_REQUEST_PAYMENT_TIMED_OUT")
        bank = transaction.get("bank", "HDFC")
        retry_count = int(transaction.get("retry_count", 0))
        last_retry = transaction.get("last_retry_timestamp", None)

        # 1. Run ML inference engine
        ml_res = ml_engine.predict_recovery_propensity(transaction)
        p_rec = ml_res["p_recovery"]
        opt_hour = ml_res["optimal_retry_hour"]
        rec_discount = ml_res["recommended_discount_pct"]
        rec_channel = ml_res["recommended_channel"]

        # 2. Evaluate Safety Guardrails
        is_allowed, g_reason, sanitized_params = validate_recovery_guardrails(
            transaction_id=tx_id,
            amount=amount,
            current_retry_count=retry_count,
            requested_discount_pct=rec_discount,
            last_retry_timestamp=last_retry
        )

        if not is_allowed:
            # Guardrail blocked execution
            plan = {
                "recommended_action": "MANUAL_HUMAN_REVIEW",
                "confidence_score": 0.95,
                "rationale": f"Guardrail blocked automated retry: {g_reason}",
                "cascaded_channels": ["SUPPORT_TICKET_ESCALATION"],
                "approved_discount_pct": 0.0,
                "discount_amount": 0.0,
                "final_payable_amount": amount,
                "scheduled_retry_time": None,
                "guardrail_status": "BLOCKED",
                "guardrail_reason": g_reason,
                "ml_insights": ml_res
            }
            return plan

        # 3. Determine recommended action
        if error_code in ["BAD_REQUEST_PAYMENT_TIMED_OUT", "GATEWAY_ERROR"]:
            action = "SCHEDULE_SMART_RETRY" if opt_hour != int(time.strftime("%H")) else "SMART_RETRY_NOW"
            rationale = f"Bank gateway glitch detected at {bank}. Scheduling retry at optimal bank uptime window ({opt_hour:02d}:00 HRS)."
            cascaded = ["SMART_GATEWAY_RETRY", "WHATSAPP_PAYLINK"]
        elif error_code == "CUSTOMER_INSUFFICIENT_FUNDS":
            action = "OFFER_DYNAMIC_INCENTIVE" if sanitized_params["approved_discount_pct"] > 0 else "SEND_WHATSAPP_PAYLINK"
            rationale = f"Insufficient funds detected. Offering {sanitized_params['approved_discount_pct']}% dynamic incentive via WhatsApp PayLink to close recovery."
            cascaded = ["WHATSAPP_PAYLINK", "UPI_INTENT_SWAP", "SMS_PAYLINK"]
        elif error_code == "MANDATE_EXECUTION_FAILED":
            action = "SWITCH_GATEWAY_ROUTING"
            rationale = f"Recurring mandate failed. Switching card/UPI network routing and triggering secondary debit authorization."
            cascaded = ["UPI_INTENT_SWAP", "WHATSAPP_PAYLINK"]
        else:
            action = "SEND_WHATSAPP_PAYLINK"
            rationale = f"Checkout friction detected. Sending automated 1-click WhatsApp recovery link."
            cascaded = ["WHATSAPP_PAYLINK", "SMS_PAYLINK"]

        plan = {
            "recommended_action": action,
            "confidence_score": round(min(0.98, max(0.60, p_rec + 0.15)), 2),
            "rationale": rationale,
            "cascaded_channels": cascaded,
            "approved_discount_pct": sanitized_params["approved_discount_pct"],
            "discount_amount": sanitized_params["discount_amount"],
            "final_payable_amount": sanitized_params["final_payable_amount"],
            "scheduled_retry_time": f"Today at {opt_hour:02d}:00 HRS",
            "guardrail_status": "APPROVED",
            "guardrail_reason": g_reason,
            "ml_insights": ml_res
        }

        # 4. Anti-hallucination Schema Verification
        valid_schema, schema_err = validate_ai_output_schema(plan)
        if not valid_schema:
            plan["guardrail_status"] = "BLOCKED_SCHEMA_ERROR"
            plan["guardrail_reason"] = schema_err
            plan["recommended_action"] = "MANUAL_HUMAN_REVIEW"

        return plan

# Global AI agent instance
ai_agent = AIRecoveryAgent()
