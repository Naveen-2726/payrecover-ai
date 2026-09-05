import pytest
import time
from fastapi.testclient import TestClient

from app.main import app, policy_config, transactions_db
from app.core.state_machine import payment_state_machine, PaymentState
from app.core.health_engine import payment_health_engine
from app.core.error_semantics import error_semantic_engine
from app.ai.optimizer import action_optimizer
from app.ai.orchestrator import recovery_orchestrator
from app.audit.ledger import AuditLedger, mask_pii
from app.safety.guardrails import validate_ai_output_schema, validate_recovery_guardrails, check_idempotency
from app.mock_razorpay.gateway import razorpay_simulator

client = TestClient(app)

# --- PHASE 2: STATE MACHINE ADVERSARIAL TESTS ---
def test_state_machine_captured_to_failed_blocked():
    # CAPTURED -> FAILED must be REJECTED!
    is_valid, final_st, msg = payment_state_machine.transition(
        current_state=PaymentState.CAPTURED,
        target_state=PaymentState.FAILED,
        transaction_id="tx_captured_01"
    )
    assert is_valid is False
    assert final_st == PaymentState.CAPTURED
    assert "INVALID STATE TRANSITION REJECTED" in msg

def test_late_authorization_cancels_retry():
    payment_id = f"pay_late_auth_adv_{int(time.time())}"
    # Step 1: Simulated timeout failed payment
    res1 = client.post("/api/simulate/failed-payment", json={
        "event_type": "payment.failed",
        "amount": 4999.0,
        "bank": "HDFC",
        "error_code": "BAD_REQUEST_PAYMENT_TIMED_OUT",
        "payment_id_override": payment_id
    })
    assert res1.status_code == 200
    assert res1.json()["transaction"]["status"] == PaymentState.POTENTIALLY_LATE_AUTHORIZABLE

    # Step 2: Late payment.captured webhook arrives
    res2 = client.post("/api/simulate/failed-payment", json={
        "event_type": "payment.captured",
        "amount": 4999.0,
        "bank": "HDFC",
        "payment_id_override": payment_id
    })
    assert res2.status_code == 200
    assert res2.json()["transaction"]["status"] == PaymentState.RECOVERED_OR_LATE_AUTHORIZED
    assert "Recovery prevented because payment later authorized." in res2.json()["message"]


# --- PHASE 3: WEBHOOK ADVERSARIAL TESTS ---
def test_webhook_duplicate_event_zero_side_effect():
    payload, raw_bytes, sig = razorpay_simulator.generate_webhook_payload()
    headers = {"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    
    res1 = client.post("/api/webhooks/razorpay", content=raw_bytes, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "PROCESSED"

    # Replay same payload with identical event ID
    res2 = client.post("/api/webhooks/razorpay", content=raw_bytes, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["status"] == "SKIPPED"

def test_webhook_invalid_hmac_rejected():
    policy_config.require_webhook_hmac = True
    payload, raw_bytes, _ = razorpay_simulator.generate_webhook_payload()
    headers = {"X-Razorpay-Signature": "tampered_signature_hex", "Content-Type": "application/json"}
    
    res = client.post("/api/webhooks/razorpay", content=raw_bytes, headers=headers)
    assert res.status_code == 401

def test_webhook_malformed_json_rejected():
    headers = {"X-Razorpay-Signature": "sig", "Content-Type": "application/json"}
    res = client.post("/api/webhooks/razorpay", content=b"{malformed_json: missing_quotes}", headers=headers)
    assert res.status_code in [400, 401]


# --- PHASE 4: AI FAILURE & HALLUCINATION SANITIZATION TESTS ---
def test_ai_out_of_bounds_confidence_sanitization():
    invalid_plan = {
        "recommended_action": "SMART_RETRY_NOW",
        "confidence_score": 5.0,  # Invalid (> 1.0)
        "rationale": "test",
        "cascaded_channels": ["SMART_GATEWAY_RETRY"]
    }
    valid, msg = validate_ai_output_schema(invalid_plan)
    assert valid is False

def test_ai_negative_discount_sanitization():
    is_valid, reason, sanitized = validate_recovery_guardrails(
        transaction_id="tx_neg_disc",
        amount=1000.0,
        current_retry_count=0,
        requested_discount_pct=-15.0  # Negative discount
    )
    assert is_valid is True
    assert sanitized["approved_discount_pct"] >= 0.0

def test_ai_excessive_discount_capping():
    is_valid, reason, sanitized = validate_recovery_guardrails(
        transaction_id="tx_ex_disc",
        amount=1000.0,
        current_retry_count=0,
        requested_discount_pct=500.0  # 500% discount
    )
    assert is_valid is True
    assert sanitized["approved_discount_pct"] <= policy_config.max_discount_percent


# --- PHASE 5: ECONOMIC SANITY CHECK TESTS ---
def test_expected_value_economic_sanity():
    # Negative amount or zero amount
    winner_zero, candidates = action_optimizer.evaluate_candidate_actions(
        base_p_recovery=0.0,
        amount=0.0,
        failure_category="PERMANENT_PAYMENT_FAILURE"
    )
    assert winner_zero["action"] in ["NO_ACTION", "HUMAN_ESCALATION"]
    assert winner_zero["expected_value_score"] <= 0.0

def test_no_action_wins_when_all_ev_negative():
    winner, candidates = action_optimizer.evaluate_candidate_actions(
        base_p_recovery=0.01,
        amount=10.0,
        failure_category="PERMANENT_PAYMENT_FAILURE",
        discount_pct=0.0
    )
    assert winner["action"] in ["NO_ACTION", "HUMAN_ESCALATION"]


# --- PHASE 13: AUDIT TAMPER DETECTION TESTS ---
def test_audit_ledger_tamper_detection_full():
    ledger = AuditLedger()
    ledger.append_event("WEBHOOK", "tx_1", {"amt": 100})
    ledger.append_event("RETRY", "tx_1", {"amt": 100})
    assert ledger.verify_integrity() is True

    # Mutate Block 1 payload
    ledger.chain[1]["details"]["amt"] = 999999
    assert ledger.verify_integrity() is False  # Tamper detected!

    # Restore correct payload
    ledger.chain[1]["details"]["amt"] = 100
    assert ledger.verify_integrity() is True  # Valid again!


# --- PHASE 19: PERFORMANCE BENCHMARK TEST ---
def test_performance_benchmark_500_transactions():
    t0 = time.time()
    for i in range(500):
        tx = {
            "id": f"tx_perf_{i}",
            "amount": 1000.0 + i,
            "bank": "HDFC" if i % 2 == 0 else "SBI",
            "error_code": "BAD_REQUEST_PAYMENT_TIMED_OUT" if i % 3 == 0 else "CUSTOMER_INSUFFICIENT_FUNDS",
            "retry_count": 0
        }
        res = recovery_orchestrator.orchestrate_recovery(tx)
        assert res["payment_id"] == f"tx_perf_{i}"
    t1 = time.time()
    duration = t1 - t0
    print(f"500 Transactions Orchestration Duration: {duration:.2f} seconds ({duration/500*1000:.2f} ms/tx)")
    assert duration < 10.0  # Must process 500 transactions in under 10 seconds (<20ms per transaction)
