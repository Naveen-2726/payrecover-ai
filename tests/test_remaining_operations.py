from fastapi.testclient import TestClient

from app.ai.customer_recovery import customer_recovery
from app.ai.memory import agent_memory
from app.ai.recovery_budget import recovery_budget
from app.analytics.reliability_forecast import forecast_payment_reliability
from app.main import app, transactions_db


client = TestClient(app)


def test_autonomous_budget_allows_then_blocks_spend():
    original_limit = recovery_budget.daily_limit_inr
    recovery_budget.daily_limit_inr = 1.0
    recovery_budget.reset()
    assert recovery_budget.authorize("budget_1", "SMART_RETRY", 1.0)["allowed"] is True
    blocked = recovery_budget.authorize("budget_2", "SMART_RETRY", 1.0)
    assert blocked["allowed"] is False
    assert recovery_budget.status()["autonomous_actions_paused"] is True
    recovery_budget.daily_limit_inr = original_limit
    recovery_budget.reset()


def test_reliability_forecast_is_deterministic_and_ranked():
    result = forecast_payment_reliability()
    assert result["window_minutes"] == 30
    assert result["synthetic_forecast"] is True
    assert result["forecasts"]
    assert any(item["risk"] == "HIGH" for item in result["forecasts"])


def test_bounded_memory_hashes_customer_identity():
    result = agent_memory.remember("customer@example.com", "upi", "UPI_INTENT")
    assert "customer@example.com" not in result["memory_key"]
    recalled = agent_memory.recall("customer@example.com")
    assert recalled["preferred_method"] == "upi"


def test_customer_recovery_requires_explicit_consent():
    payment_id = next(iter(transactions_db))
    blocked = client.post("/api/customer-recovery/start", json={"payment_id": payment_id, "consent": False})
    assert blocked.status_code == 200
    assert blocked.json()["status"] == "BLOCKED"

    started = client.post("/api/customer-recovery/start", json={"payment_id": payment_id, "consent": True})
    assert started.json()["status"] == "AWAITING_CONFIRMATION"
    confirmed = client.post("/api/customer-recovery/confirm", json={"payment_id": payment_id, "confirmed": True})
    assert confirmed.json()["status"] == "PAYMENT_LINK_GENERATED"
    assert confirmed.json()["mock_payment_link"].startswith("https://example.invalid/")


def test_remaining_operations_are_exposed_by_api():
    assert client.get("/api/agent/budget").status_code == 200
    assert client.get("/api/agent/observability").status_code == 200
    assert client.get("/api/analytics/reliability-forecast").status_code == 200
    assert client.get("/api/agent/memory/customer@example.com").status_code == 200
