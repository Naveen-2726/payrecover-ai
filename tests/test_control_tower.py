from app.ai.policy_compiler import policy_compiler
from app.analytics.control_tower import build_recovery_control_tower
from app.reliability.lab import webhook_reliability_lab
from app.analytics.benchmark import run_ai_vs_baseline_benchmark


def test_policy_compiler_emits_executable_policy_shape():
    result = policy_compiler.compile_natural_instruction(
        "Do not retry a payment if the bank is down. Prefer UPI during card degradation. "
        "Never contact a customer more than once in 24 hours."
    )
    policy = result["structured_policy"]
    assert "conditions" in policy
    assert "allowed_actions" in policy
    assert "blocked_actions" in policy
    assert policy["contact_limits"]["window_seconds"] == 86400
    assert result["validation"]["schema_valid"] is True
    assert "RETRY_SAME_METHOD" in policy["blocked_actions"]


def test_control_tower_preserves_failed_cohort_and_calculates_incremental_value():
    transactions = [
        {
            "amount": 1000,
            "error_code": "GATEWAY_ERROR",
            "status": "RECOVERED",
            "recovered_amount": 1000,
            "orchestration": {"recovery_probability": 0.8, "action_matrix": []},
        }
    ]
    result = build_recovery_control_tower(transactions)
    metrics = result["metrics"]
    assert metrics["failed_payment_value_inr"] == 1000
    assert metrics["baseline_expected_recovery_inr"] == 300
    assert metrics["incremental_recovered_revenue_inr"] == 700
    assert metrics["payment_cohort_incremental_recovered_revenue_inr"] == 700


def test_benchmark_explicitly_does_not_fabricate_confidence_intervals():
    result = run_ai_vs_baseline_benchmark(30)
    assert result["confidence_intervals"]["status"] == "NOT_REPORTED"
    assert "not reported" in result["confidence_intervals"]["message"]


def test_reliability_judge_evidence_is_actual_and_complete():
    result = webhook_reliability_lab.get_judge_evidence()
    assert result["all_passed"] is True
    assert {item["attack_type"] for item in result["results"]} >= {
        "DUPLICATE_EVENT", "OUT_OF_ORDER", "INVALID_SIGNATURE",
        "DELAYED_EVENT", "LATE_AUTHORIZATION",
    }
    assert all(item["audit_event"] for item in result["results"])