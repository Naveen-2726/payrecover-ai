from typing import Any, Dict

from app.audit.ledger import ledger_instance
from app.analytics.payment_intelligence import diagnose_payment


class ConsentGatedCustomerRecovery:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def start(self, transaction: Dict[str, Any], consent: bool) -> Dict[str, Any]:
        transaction_id = str(transaction.get("id"))
        if not consent:
            result = {"status": "BLOCKED", "reason": "Explicit customer consent is required before customer-facing recovery.", "payment_id": transaction_id}
            ledger_instance.append_event("CUSTOMER_RECOVERY_CONSENT_BLOCKED", transaction_id, result)
            return result
        diagnosis = diagnose_payment(transaction)
        session = {
            "payment_id": transaction_id,
            "status": "AWAITING_CONFIRMATION",
            "message": "I found the failed payment. Confirm to generate the synthetic recovery link.",
            "diagnosis": diagnosis["diagnosis"],
            "synthetic_demo_data": True,
        }
        self.sessions[transaction_id] = session
        ledger_instance.append_event("CUSTOMER_RECOVERY_CONSENT_GRANTED", transaction_id, {"status": session["status"]})
        return session

    def confirm(self, transaction_id: str, confirmed: bool) -> Dict[str, Any]:
        session = self.sessions.get(transaction_id)
        if not session:
            return {"status": "NOT_FOUND", "payment_id": transaction_id}
        if not confirmed:
            session["status"] = "CANCELLED"
            ledger_instance.append_event("CUSTOMER_RECOVERY_CANCELLED", transaction_id, {})
            return session
        session["status"] = "PAYMENT_LINK_GENERATED"
        session["mock_payment_link"] = f"https://example.invalid/payrecover/{transaction_id}"
        ledger_instance.append_event("CUSTOMER_RECOVERY_LINK_GENERATED", transaction_id, {"status": session["status"]})
        return session


customer_recovery = ConsentGatedCustomerRecovery()
