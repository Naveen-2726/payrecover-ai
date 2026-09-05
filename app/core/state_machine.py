from typing import Dict, Any, Tuple, Optional, List
import time

class PaymentState:
    CREATED = "CREATED"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    POTENTIALLY_LATE_AUTHORIZABLE = "POTENTIALLY_LATE_AUTHORIZABLE"
    RECOVERY_PENDING = "RECOVERY_PENDING"
    RECOVERY_ATTEMPTED = "RECOVERY_ATTEMPTED"
    RECOVERED = "RECOVERED"
    RECOVERED_OR_LATE_AUTHORIZED = "RECOVERED_OR_LATE_AUTHORIZED"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class PaymentStateMachine:
    """
    Deterministic Payment State Machine enforcing valid Razorpay lifecycle transitions.
    Rejects invalid state mutations (e.g. CAPTURED -> FAILED).
    """

    VALID_TRANSITIONS = {
        PaymentState.CREATED: [
            PaymentState.AUTHORIZED,
            PaymentState.CAPTURED,
            PaymentState.FAILED,
            PaymentState.POTENTIALLY_LATE_AUTHORIZABLE
        ],
        PaymentState.FAILED: [
            PaymentState.POTENTIALLY_LATE_AUTHORIZABLE,
            PaymentState.RECOVERY_PENDING,
            PaymentState.ESCALATED,
            PaymentState.CLOSED
        ],
        PaymentState.POTENTIALLY_LATE_AUTHORIZABLE: [
            PaymentState.RECOVERED_OR_LATE_AUTHORIZED,
            PaymentState.RECOVERY_PENDING,
            PaymentState.FAILED,
            PaymentState.ESCALATED
        ],
        PaymentState.RECOVERY_PENDING: [
            PaymentState.RECOVERY_ATTEMPTED,
            PaymentState.RECOVERED_OR_LATE_AUTHORIZED,
            PaymentState.ESCALATED,
            PaymentState.CLOSED
        ],
        PaymentState.RECOVERY_ATTEMPTED: [
            PaymentState.RECOVERED,
            PaymentState.RECOVERY_PENDING,
            PaymentState.ESCALATED,
            PaymentState.CLOSED
        ],
        PaymentState.AUTHORIZED: [
            PaymentState.CAPTURED,
            PaymentState.FAILED
        ],
        PaymentState.CAPTURED: [
            PaymentState.CLOSED
        ],
        PaymentState.RECOVERED: [
            PaymentState.CLOSED
        ],
        PaymentState.RECOVERED_OR_LATE_AUTHORIZED: [
            PaymentState.CLOSED
        ],
        PaymentState.ESCALATED: [
            PaymentState.RECOVERED,
            PaymentState.CLOSED
        ],
        PaymentState.CLOSED: []
    }

    def transition(
        self,
        current_state: str,
        target_state: str,
        transaction_id: str,
        event_reason: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """
        Attempts to transition transaction from current_state to target_state.
        Returns (is_valid, final_state, reason_message)
        """
        curr = (current_state or PaymentState.CREATED).upper()
        target = (target_state or PaymentState.FAILED).upper()

        if curr == target:
            return True, curr, f"No-op transition: state remains {curr}"

        allowed = self.VALID_TRANSITIONS.get(curr, [])
        if target not in allowed:
            reason = f"INVALID STATE TRANSITION REJECTED: Cannot transition payment {transaction_id} from {curr} -> {target}. Allowed transitions from {curr}: {allowed}"
            return False, curr, reason

        reason = f"Transition approved: {curr} -> {target}. Reason: {event_reason or 'State machine update'}"
        return True, target, reason

payment_state_machine = PaymentStateMachine()
