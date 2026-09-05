from fastapi.testclient import TestClient

from app.audit.ledger import ledger_instance
from app.main import app, transactions_db


client = TestClient(app)


def test_payment_intelligence_returns_context_and_diagnosis():
    transaction_id = next(iter(transactions_db))
    result = client.get(f"/api/transactions/{transaction_id}/intelligence")
    assert result.status_code == 200
    data = result.json()
    assert data["context"]["gateway_health"]["status"] in {"HEALTHY", "DEGRADED", "DOWN"}
    assert data["diagnosis"]["recovery_probability_pct"]
    assert data["diagnosis"]["best_action"]
    assert data["synthetic_context"] is True


def test_opportunities_are_ranked_and_include_subscription_records():
    result = client.get("/api/analytics/opportunities")
    assert result.status_code == 200
    data = result.json()
    values = [item["opportunity_value_inr"] for item in data["opportunities"]]
    assert values == sorted(values, reverse=True)
    assert any(item["source"] == "subscription" for item in data["opportunities"])


def test_replay_is_estimate_only_and_audited():
    transaction_id = next(iter(transactions_db))
    result = client.post(f"/api/transactions/{transaction_id}/replay", json={})
    assert result.status_code == 200
    data = result.json()
    assert data["synthetic_replay"] is True
    assert data["alternative"]["estimate_only"] is True
    assert data["timeline"]
    assert any(event["event"] == "RECOVERY_DECISION_REPLAYED" for event in ledger_instance.get_transaction_history(transaction_id))
