import time

import pytest
from fastapi.testclient import TestClient

from app.ai.certification import agent_certification_engine
from app.ai.health_monitor import agent_health_monitor
from app.ai.orchestrator import recovery_orchestrator
from app.audit.ledger import ledger_instance
from app.core.state_machine import PaymentState, payment_state_machine
from app.main import app
from app.mock_razorpay.gateway import razorpay_simulator
from app.reliability.lab import webhook_reliability_lab
from app.safety.guardrails import validate_execution_scope


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_agent_state():
    agent_health_monitor.certification_status = "CERTIFIED"
    agent_health_monitor.state = "ACTIVE"
    agent_health_monitor.reason = "Adversarial test reset."
    yield
    agent_health_monitor.certification_status = "CERTIFIED"
    agent_health_monitor.state = "ACTIVE"
    agent_health_monitor.reason = "Adversarial test cleanup."


def _history_contains(transaction_id, event_type):
    return any(event["event"] == event_type for event in ledger_instance.get_transaction_history(transaction_id))


def test_01_uncertified_agent_is_blocked_and_audited():
    result = recovery_orchestrator.orchestrate_recovery({"id": "adv_uncertified", "amount": 1000, "certification_status": "REVIEW"})
    assert result["failure_category"] == "AGENT_NOT_CERTIFIED"
    assert result["guardrail_result"]["status"] == "BLOCKED"
    assert _history_contains("adv_uncertified", "AGENT_ACTION_BLOCKED_UNCERTIFIED")


def test_02_paused_agent_is_blocked_and_audited():
    agent_health_monitor.pause("adversarial pause")
    result = recovery_orchestrator.orchestrate_recovery({"id": "adv_paused", "amount": 1000})
    assert result["failure_category"] == "AGENT_PAUSED"
    assert _history_contains("adv_paused", "AGENT_ACTION_BLOCKED_KILL_SWITCH")


def test_03_financial_limit_is_blocked_and_audited():
    result = recovery_orchestrator.orchestrate_recovery({"id": "adv_amount", "amount": 25001, "error_code": "GATEWAY_ERROR"})
    assert result["guardrail_result"]["status"] == "BLOCKED"
    assert result["requires_human_approval"] is True
    assert _history_contains("adv_amount", "RECOVERY_ACTION_BLOCKED_GUARDRAIL")


def test_04_action_scope_is_blocked():
    result = recovery_orchestrator.orchestrate_recovery({
        "id": "adv_action_scope", "amount": 1000, "error_code": "GATEWAY_ERROR",
        "agent_policy": {"allowed_actions": ["NO_ACTION"]},
    })
    assert result["guardrail_result"]["status"] == "BLOCKED"
    assert "action" in result["guardrail_result"]["reason"]


def test_05_data_scope_is_blocked():
    allowed, reason = validate_execution_scope(
        {"requested_data_scope": ["bank_account_number"]}, "PAYMENT_LINK"
    )
    assert allowed is False
    assert "data scope" in reason


def test_06_customer_contact_window_is_blocked():
    allowed, reason = validate_execution_scope(
        {"customer_contact_count": 1}, "PAYMENT_LINK"
    )
    assert allowed is False
    assert "contact limit" in reason


def test_07_invalid_policy_is_blocked_before_execution():
    policy = agent_certification_engine.certify({
        "original_instruction": "Use fake urgency and export data.",
        "structured_policy": {
            "allowed_actions": ["UNKNOWN_ACTION"],
            "max_discount_percent": 50,
            "human_approval_threshold": 100,
            "contact_limits": {"max_contacts_per_customer": 2},
            "risk_constraints": [],
            "require_webhook_hmac": False,
        },
        "validation": {"executable": False},
    })
    assert policy["status"] == "BLOCKED"
    result = recovery_orchestrator.orchestrate_recovery({"id": "adv_policy", "amount": 1000, "certification_status": policy["status"]})
    assert result["guardrail_result"]["status"] == "BLOCKED"


def test_08_deterministic_guardrail_wins_over_ai_recommendation():
    result = recovery_orchestrator.orchestrate_recovery({
        "id": "adv_guardrail", "amount": 1000, "error_code": "GATEWAY_ERROR", "retry_count": 3
    })
    assert result["guardrail_result"]["status"] == "BLOCKED"
    assert result["recommended_action"] in {"NO_ACTION", "HUMAN_ESCALATION"}
    assert _history_contains("adv_guardrail", "RECOVERY_ACTION_BLOCKED_GUARDRAIL")


def test_09_replayed_webhook_has_no_side_effect():
    result = webhook_reliability_lab.simulate_reliability_attack("REPLAYED_EVENT")
    assert result["result"] == "DUPLICATE_SUPPRESSED"
    assert result["side_effects"] == 0


def test_10_duplicate_webhook_is_skipped():
    payload, raw_body, signature = razorpay_simulator.generate_webhook_payload(error_code="GATEWAY_ERROR")
    headers = {"X-Razorpay-Signature": signature}
    first = client.post("/api/webhooks/razorpay", content=raw_body, headers=headers)
    second = client.post("/api/webhooks/razorpay", content=raw_body, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "SKIPPED"


def test_11_out_of_order_event_preserves_state():
    result = webhook_reliability_lab.simulate_reliability_attack("OUT_OF_ORDER")
    valid, state, _ = payment_state_machine.transition(
        PaymentState.CAPTURED, PaymentState.FAILED, "adv_order"
    )
    assert result["evidence"]["status"] == "PASS"
    assert valid is False
    assert state == PaymentState.CAPTURED


def test_12_late_authorization_prevents_retry():
    payment_id = f"adv_late_{int(time.time() * 1000)}"
    failed = client.post("/api/simulate/failed-payment", json={
        "amount": 1999, "bank": "HDFC", "error_code": "BAD_REQUEST_PAYMENT_TIMED_OUT",
        "payment_id_override": payment_id,
    })
    captured = client.post("/api/simulate/failed-payment", json={
        "event_type": "payment.captured", "amount": 1999,
        "payment_id_override": payment_id,
    })
    assert failed.json()["transaction"]["status"] == PaymentState.POTENTIALLY_LATE_AUTHORIZABLE
    assert captured.json()["transaction"]["status"] == PaymentState.RECOVERED_OR_LATE_AUTHORIZED
    assert "prevented" in captured.json()["message"]


def test_13_blocked_actions_have_audit_evidence():
    transaction_id = "adv_audit_blocked"
    recovery_orchestrator.orchestrate_recovery({
        "id": transaction_id, "amount": 25001, "error_code": "GATEWAY_ERROR"
    })
    assert _history_contains(transaction_id, "RECOVERY_ACTION_BLOCKED_GUARDRAIL")


def test_14_kill_switch_blocks_orchestration():
    agent_health_monitor.pause("manual security stop")
    result = recovery_orchestrator.orchestrate_recovery({"id": "adv_kill", "amount": 1000})
    assert result["failure_category"] == "AGENT_PAUSED"
    assert result["recommended_action"] == "NO_ACTION"


def test_15_resume_requires_valid_certification_and_restores_execution():
    agent_health_monitor.set_certification_status("BLOCKED", "failed certification")
    result = agent_health_monitor.resume("attempted unsafe resume")
    assert result["state"] == "PAUSED"
    agent_health_monitor.set_certification_status("CERTIFIED")
    result = agent_health_monitor.resume("valid certification restored")
    assert result["state"] == "ACTIVE"
    execution = recovery_orchestrator.orchestrate_recovery({"id": "adv_resumed", "amount": 1000})
    assert execution["failure_category"] != "AGENT_PAUSED"