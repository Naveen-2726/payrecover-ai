import pytest
from app.core.state_machine import payment_state_machine, PaymentState
from app.core.health_engine import payment_health_engine
from app.core.error_semantics import error_semantic_engine
from app.ai.orchestrator import recovery_orchestrator
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_state_machine_valid_transitions():
    is_valid, new_st, msg = payment_state_machine.transition(
        current_state=PaymentState.FAILED,
        target_state=PaymentState.POTENTIALLY_LATE_AUTHORIZABLE,
        transaction_id="tx_test_valid"
    )
    assert is_valid is True
    assert new_st == PaymentState.POTENTIALLY_LATE_AUTHORIZABLE

def test_state_machine_invalid_transition_rejection():
    # CAPTURED -> FAILED must be REJECTED!
    is_valid, final_st, msg = payment_state_machine.transition(
        current_state=PaymentState.CAPTURED,
        target_state=PaymentState.FAILED,
        transaction_id="tx_test_invalid"
    )
    assert is_valid is False
    assert final_st == PaymentState.CAPTURED  # State unchanged
    assert "INVALID STATE TRANSITION REJECTED" in msg

def test_payment_health_engine_eval():
    health = payment_health_engine.evaluate_health("SBI", "netbanking")
    assert health["status"] in ["HEALTHY", "DEGRADED", "DOWN"]
    assert "success_rate_pct" in health

def test_error_semantics_classification():
    sem = error_semantic_engine.analyze_error_semantics("BAD_REQUEST_PAYMENT_TIMED_OUT")
    assert sem["category"] == "POTENTIALLY_LATE_AUTHORIZABLE"
    assert sem["late_authorization_risk"] == "HIGH"

def test_late_authorization_protection_flow():
    tx = {
        "id": "tx_test_late_auth",
        "amount": 4999.0,
        "bank": "HDFC",
        "error_code": "BAD_REQUEST_PAYMENT_TIMED_OUT",
        "status": PaymentState.FAILED
    }
    orch = recovery_orchestrator.orchestrate_recovery(tx)
    assert orch["late_authorization_protected"] is True
    assert orch["current_state"] == PaymentState.POTENTIALLY_LATE_AUTHORIZABLE

def test_api_deterministic_scenarios():
    res = client.post("/api/demo/scenario/SCENARIO_1")
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"

    res3 = client.post("/api/demo/scenario/SCENARIO_3")
    assert res3.status_code == 200

def test_api_attribution_and_feedback():
    res_attr = client.get("/api/analytics/attribution")
    assert res_attr.status_code == 200
    data_attr = res_attr.json()
    assert "Smart Retry" in data_attr

    res_fb = client.get("/api/analytics/feedback")
    assert res_fb.status_code == 200
    data_fb = res_fb.json()
    assert "prediction_error_mae" in data_fb
