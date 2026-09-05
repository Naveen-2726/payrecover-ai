from typing import Any, Dict

from app.core.health_engine import payment_health_engine


def forecast_payment_reliability(window_minutes: int = 30) -> Dict[str, Any]:
    """Create a deterministic near-term forecast from the existing health matrix."""
    forecasts = []
    for bank, methods in payment_health_engine.health_matrix.items():
        for method, current_rate in methods.items():
            status = "HEALTHY" if current_rate >= 0.80 else "DEGRADED" if current_rate >= 0.50 else "DOWN"
            change = 0.08 if status != "HEALTHY" else 0.02
            expected_rate = max(0.0, current_rate - change)
            risk = "HIGH" if expected_rate < 0.60 else "MEDIUM" if expected_rate < 0.80 else "LOW"
            forecasts.append({
                "bank": bank,
                "payment_method": method,
                "current_success_rate_pct": round(current_rate * 100, 1),
                "expected_success_rate_pct": round(expected_rate * 100, 1),
                "trend": "DOWN",
                "risk": risk,
                "window_minutes": window_minutes,
            })
    forecasts.sort(key=lambda item: (item["risk"] != "HIGH", item["expected_success_rate_pct"]))
    return {"window_minutes": window_minutes, "forecasts": forecasts, "synthetic_forecast": True}
