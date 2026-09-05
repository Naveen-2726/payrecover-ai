from app.ai.health_monitor import agent_health_monitor
from app.ai.orchestrator import recovery_orchestrator
from app.analytics.agent_sandbox import run_agent_sandbox
from app.ai.certification import agent_certification_engine


def test_agent_certification_passes_safe_compiled_policy():
    result = agent_certification_engine.certify({
        "original_instruction": "Use bounded recovery actions.",
        "structured_policy": {
            "allowed_actions": ["RETRY_SAME_METHOD", "SEND_PAYMENT_LINK", "HUMAN_REVIEW"],
            "max_discount_percent": 10,
            "human_approval_threshold": 25000,
            "contact_limits": {"max_contacts_per_customer": 1},
            "risk_constraints": ["respect_late_authorization"],
            "require_webhook_hmac": True,
        },
        "validation": {"executable": True},
    })
    assert result["status"] == "CERTIFIED"
    assert result["audit_coverage_pct"] == 100


def test_agent_sandbox_is_reproducible_and_safe():
    first = run_agent_sandbox(20)
    second = run_agent_sandbox(20)
    assert first["transactions_evaluated"] == 20
    assert first["unsafe_actions"] == 0
    assert first["expected_recovery_inr"] == second["expected_recovery_inr"]
    assert first["actual_recovery_rate_pct"] == second["actual_recovery_rate_pct"]


def test_kill_switch_blocks_and_resume_restores_orchestration():
    agent_health_monitor.pause("test pause")
    paused = recovery_orchestrator.orchestrate_recovery({"id": "tx_paused", "amount": 1000})
    assert paused["failure_category"] == "AGENT_PAUSED"
    assert paused["guardrail_result"]["status"] == "BLOCKED"

    agent_health_monitor.resume("test cleanup")
    resumed = recovery_orchestrator.orchestrate_recovery({"id": "tx_resumed", "amount": 1000})
    assert resumed["payment_id"] == "tx_resumed"
    assert resumed["failure_category"] != "AGENT_PAUSED"