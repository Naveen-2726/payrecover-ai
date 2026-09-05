import pytest
from app.ai.classifier import failure_classifier
from app.ai.optimizer import action_optimizer
from app.ai.orchestrator import recovery_orchestrator
from app.analytics.benchmark import run_ai_vs_baseline_benchmark
from app.analytics.simulator import strategy_simulator

def test_failure_classifier():
    cat, desc, strat = failure_classifier.classify("BAD_REQUEST_PAYMENT_TIMED_OUT")
    assert cat == "TEMPORARY"
    
    cat, desc, strat = failure_classifier.classify("CUSTOMER_INSUFFICIENT_FUNDS")
    assert cat == "CUSTOMER_ACTION_REQUIRED"

    cat, desc, strat = failure_classifier.classify("EXPIRED_CARD")
    assert cat == "PERMANENT"

def test_ev_action_optimizer():
    winner, candidates = action_optimizer.evaluate_candidate_actions(
        base_p_recovery=0.85,
        amount=2500.0,
        failure_category="TEMPORARY",
        discount_pct=0.0
    )
    assert winner is not None
    assert "expected_value_score" in winner
    assert len(candidates) == 7

def test_ai_orchestrator():
    tx = {
        "id": "tx_test_orch",
        "amount": 3500.0,
        "bank": "HDFC",
        "error_code": "BAD_REQUEST_PAYMENT_TIMED_OUT",
        "retry_count": 0
    }
    res = recovery_orchestrator.orchestrate_recovery(tx)
    assert res["payment_id"] == "tx_test_orch"
    assert res["failure_category"] == "POTENTIALLY_LATE_AUTHORIZABLE"
    assert "expected_recovery_value" in res
    assert "feature_contributions" in res

def test_ai_vs_baseline_benchmark():
    res = run_ai_vs_baseline_benchmark(30)
    assert "baseline" in res
    assert "payrecover_ai" in res
    assert "uplift" in res
    assert res["payrecover_ai"]["recovery_rate_pct"] >= res["baseline"]["recovery_rate_pct"]

def test_strategy_simulator():
    sim = strategy_simulator.simulate_custom_policy(
        max_retries=3,
        cooloff_seconds=7200,
        max_discount_pct=10.0,
        num_transactions=40
    )
    assert "results" in sim
    assert "recovery_rate_pct" in sim["results"]
