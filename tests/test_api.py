import pytest
from fastapi.testclient import TestClient
from app.main import app, policy_config
from app.mock_razorpay.gateway import razorpay_simulator

client = TestClient(app)

def test_api_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["ml_model_loaded"] is True
    assert data["ledger_integrity"] is True

def test_api_analytics_endpoint():
    res = client.get("/api/analytics")
    assert res.status_code == 200
    data = res.json()
    assert "total_failed_volume_inr" in data
    assert "total_recovered_revenue_inr" in data
    assert "recovery_rate_pct" in data

def test_api_control_tower_is_transaction_derived():
    res = client.get("/api/analytics/control-tower")
    assert res.status_code == 200
    data = res.json()
    assert data["record_count"] >= 3
    metrics = data["metrics"]
    assert metrics["failed_payment_value_inr"] > 0
    assert "incremental_recovered_revenue_inr" in metrics
    assert "baseline_expected_recovery_inr" in metrics

def test_api_simulate_failed_payment():
    payload = {
        "event_type": "payment.failed",
        "amount": 2999.0,
        "bank": "HDFC",
        "error_code": "BAD_REQUEST_PAYMENT_TIMED_OUT",
        "customer_email": "api_test@example.com",
        "customer_phone": "+919876543210"
    }
    res = client.post("/api/simulate/failed-payment", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "hmac_signature" in data
    assert data["transaction"]["status"] == "POTENTIALLY_LATE_AUTHORIZABLE"

def test_api_razorpay_webhook_valid_hmac():
    payload, raw_bytes, signature = razorpay_simulator.generate_webhook_payload(
        event_type="payment.failed",
        amount=1499.0,
        bank="ICICI",
        error_code="CUSTOMER_INSUFFICIENT_FUNDS"
    )
    headers = {"X-Razorpay-Signature": signature, "Content-Type": "application/json"}
    res = client.post("/api/webhooks/razorpay", content=raw_bytes, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PROCESSED"

def test_api_razorpay_webhook_invalid_hmac():
    policy_config.require_webhook_hmac = True
    payload, raw_bytes, _ = razorpay_simulator.generate_webhook_payload()
    headers = {"X-Razorpay-Signature": "invalid_signature", "Content-Type": "application/json"}
    res = client.post("/api/webhooks/razorpay", content=raw_bytes, headers=headers)
    assert res.status_code == 401
