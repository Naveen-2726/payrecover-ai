import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any
from app.ml.train import train_and_save_models

class RecoveryMLEngine:
    def __init__(self, model_path: str = "models/recovery_model.pkl"):
        self.model_path = model_path
        self.classifier = None
        self.regressor = None
        self.load_or_train_model()

    def load_or_train_model(self):
        """Load trained models or train new ones if missing."""
        if not os.path.exists(self.model_path):
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            train_and_save_models(os.path.dirname(self.model_path))
            
        try:
            with open(self.model_path, "rb") as f:
                saved = pickle.load(f)
                self.classifier = saved["classifier"]
                self.regressor = saved["regressor"]
        except Exception:
            # Fallback training if file corrupted
            train_and_save_models(os.path.dirname(self.model_path))
            with open(self.model_path, "rb") as f:
                saved = pickle.load(f)
                self.classifier = saved["classifier"]
                self.regressor = saved["regressor"]

    def predict_recovery_propensity(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate transaction ML features and return recovery propensity, optimal retry window, 
        and dynamic incentive recommendation.
        """
        bank = transaction.get("bank", "HDFC").upper()
        payment_method = transaction.get("payment_method", "upi_intent").lower()
        error_code = transaction.get("error_code", "BAD_REQUEST_PAYMENT_TIMED_OUT")
        customer_tier = transaction.get("customer_tier", "STARTER").upper()
        amount = float(transaction.get("amount", 500.0))
        hour_of_day = int(transaction.get("hour_of_day", 14))
        day_of_month = int(transaction.get("day_of_month", 15))
        retry_count = int(transaction.get("retry_count", 0))
        is_salary_week = 1 if (1 <= day_of_month <= 7 or 28 <= day_of_month <= 31) else 0

        input_df = pd.DataFrame([{
            "bank": bank,
            "payment_method": payment_method,
            "error_code": error_code,
            "customer_tier": customer_tier,
            "amount": amount,
            "hour_of_day": hour_of_day,
            "day_of_month": day_of_month,
            "is_salary_week": is_salary_week,
            "retry_count": retry_count
        }])

        if self.classifier:
            probs = self.classifier.predict_proba(input_df)[0]
            p_recovery = float(probs[1]) if len(probs) > 1 else float(probs[0])
        else:
            p_recovery = 0.50

        if self.regressor:
            opt_hour = float(self.regressor.predict(input_df)[0])
            opt_hour = int(round(opt_hour)) % 24
        else:
            opt_hour = (hour_of_day + 2) % 24

        # Net Utility Optimization for dynamic discount %
        # We only offer a discount if recovery probability without discount is moderate-to-low (< 0.65)
        # and transaction amount is sufficient (>= ₹100)
        recommended_discount = 0.0
        if amount >= 100.0:
            if p_recovery < 0.35:
                recommended_discount = 10.0  # Max incentive for high churn risk
            elif p_recovery < 0.55:
                recommended_discount = 5.0   # Moderate incentive
            elif p_recovery < 0.70:
                recommended_discount = 2.0   # Small nudge

        # Dynamic channel routing selection
        if error_code in ["BAD_REQUEST_PAYMENT_TIMED_OUT", "GATEWAY_ERROR"]:
            recommended_channel = "SMART_GATEWAY_RETRY"
        elif error_code == "CUSTOMER_INSUFFICIENT_FUNDS":
            recommended_channel = "WHATSAPP_PAYLINK_INCENTIVE"
        elif error_code in ["AUTHENTICATION_FAILED", "OTP_TIMEOUT"]:
            recommended_channel = "SMS_PAYLINK_1CLICK"
        elif error_code == "MANDATE_EXECUTION_FAILED":
            recommended_channel = "UPI_INTENT_SWAP"
        else:
            recommended_channel = "WHATSAPP_PAYLINK"

        return {
            "p_recovery": round(p_recovery, 4),
            "p_recovery_percentage": f"{round(p_recovery * 100, 1)}%",
            "optimal_retry_hour": opt_hour,
            "optimal_retry_time_str": f"{opt_hour:02d}:00 HRS",
            "recommended_discount_pct": recommended_discount,
            "recommended_channel": recommended_channel,
            "churn_risk_level": "HIGH" if p_recovery < 0.4 else ("MEDIUM" if p_recovery < 0.7 else "LOW")
        }

# Global ML engine instance
ml_engine = RecoveryMLEngine()
