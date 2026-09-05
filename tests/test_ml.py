import pytest
from app.ml.engine import ml_engine

def test_ml_propensity_inference():
    tx = {
        "bank": "HDFC",
        "payment_method": "upi_intent",
        "error_code": "BAD_REQUEST_PAYMENT_TIMED_OUT",
        "customer_tier": "GROWTH",
        "amount": 2500.0,
        "hour_of_day": 14,
        "day_of_month": 5,
        "retry_count": 0
    }
    res = ml_engine.predict_recovery_propensity(tx)
    assert "p_recovery" in res
    assert 0.0 <= res["p_recovery"] <= 1.0
    assert "optimal_retry_hour" in res
    assert 0 <= res["optimal_retry_hour"] <= 23
    assert "churn_risk_level" in res

def test_ml_dynamic_discount_logic():
    # Low amount should not get discount
    tx_small = {"amount": 50.0, "error_code": "CUSTOMER_INSUFFICIENT_FUNDS"}
    res_small = ml_engine.predict_recovery_propensity(tx_small)
    assert res_small["recommended_discount_pct"] == 0.0
