import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

def generate_synthetic_dataset(num_samples: int = 1500) -> pd.DataFrame:
    """Generate realistic Indian payment failure dataset for training PayRecover ML models."""
    np.random.seed(42)
    
    banks = ["HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "YES_BANK", "OTHER"]
    payment_methods = ["upi_intent", "upi_autopay", "credit_card", "debit_card", "netbanking", "enach"]
    error_codes = [
        "BAD_REQUEST_PAYMENT_TIMED_OUT",
        "GATEWAY_ERROR",
        "CUSTOMER_INSUFFICIENT_FUNDS",
        "AUTHENTICATION_FAILED",
        "EXPIRED_CARD",
        "MANDATE_EXECUTION_FAILED",
        "OTP_TIMEOUT"
    ]
    customer_tiers = ["ENTERPRISE", "GROWTH", "STARTER", "RETAIL"]
    
    data = []
    for i in range(num_samples):
        bank = np.random.choice(banks, p=[0.25, 0.20, 0.20, 0.15, 0.10, 0.05, 0.05])
        method = np.random.choice(payment_methods, p=[0.35, 0.20, 0.20, 0.10, 0.10, 0.05])
        error = np.random.choice(error_codes, p=[0.25, 0.20, 0.25, 0.10, 0.05, 0.10, 0.05])
        tier = np.random.choice(customer_tiers, p=[0.10, 0.25, 0.40, 0.25])
        
        amount = round(float(np.random.exponential(scale=1500) + 100), 2)
        hour_of_day = int(np.random.randint(0, 24))
        day_of_month = int(np.random.randint(1, 31))
        
        is_salary_week = 1 if (1 <= day_of_month <= 7 or 28 <= day_of_month <= 31) else 0
        retry_count = int(np.random.choice([0, 1, 2], p=[0.7, 0.2, 0.1]))
        
        # Calculate synthetic recovery probability based on real dynamics
        base_prob = 0.50
        if error == "CUSTOMER_INSUFFICIENT_FUNDS":
            base_prob -= 0.25
            if is_salary_week:
                base_prob += 0.35  # High recovery after salary credit
        elif error in ["BAD_REQUEST_PAYMENT_TIMED_OUT", "GATEWAY_ERROR"]:
            base_prob += 0.30  # High recovery on bank uptime recovery
        elif error == "EXPIRED_CARD":
            base_prob -= 0.40
        elif error == "OTP_TIMEOUT":
            base_prob += 0.25
            
        if bank in ["HDFC", "ICICI"] and method == "upi_intent":
            base_prob += 0.10
        if tier == "ENTERPRISE":
            base_prob += 0.15
            
        recovery_prob = np.clip(base_prob, 0.05, 0.95)
        recovered = 1 if np.random.rand() < recovery_prob else 0
        
        # Optimal retry hour target
        if error == "CUSTOMER_INSUFFICIENT_FUNDS":
            optimal_hour = 10 if is_salary_week else 14  # Morning 10 AM post salary
        elif bank == "SBI":
            optimal_hour = 11  # Post SBI morning maintenance window
        else:
            optimal_hour = (hour_of_day + 3) % 24  # 3 hours off-peak delay
            
        data.append({
            "bank": bank,
            "payment_method": method,
            "error_code": error,
            "customer_tier": tier,
            "amount": amount,
            "hour_of_day": hour_of_day,
            "day_of_month": day_of_month,
            "is_salary_week": is_salary_week,
            "retry_count": retry_count,
            "recovered": recovered,
            "optimal_hour": optimal_hour
        })
        
    return pd.DataFrame(data)


def train_and_save_models(model_dir: str = "models") -> str:
    """Train recovery propensity classifier and optimal hour regressor."""
    os.makedirs(model_dir, exist_ok=True)
    df = generate_synthetic_dataset(1500)
    
    categorical_features = ["bank", "payment_method", "error_code", "customer_tier"]
    numeric_features = ["amount", "hour_of_day", "day_of_month", "is_salary_week", "retry_count"]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features)
        ]
    )
    
    X = df[numeric_features + categorical_features]
    y_recovered = df["recovered"]
    y_optimal_hour = df["optimal_hour"]
    
    clf = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42))
    ])
    clf.fit(X, y_recovered)
    
    reg = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=50, random_state=42))
    ])
    reg.fit(X, y_optimal_hour)
    
    model_path = os.path.join(model_dir, "recovery_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({"classifier": clf, "regressor": reg, "features": numeric_features + categorical_features}, f)
        
    return model_path

if __name__ == "__main__":
    path = train_and_save_models()
    print(f"Models successfully trained and saved to {path}")
