import os
import json
import numpy as np
import pandas as pd
from app.ml.train import generate_synthetic_dataset, train_and_save_models
from app.ml.engine import RecoveryMLEngine
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def evaluate_real_ml_performance(num_test_samples: int = 100):
    """
    Evaluate trained ML model on 100 test transaction records and output real metrics.
    """
    engine = RecoveryMLEngine()
    test_df = generate_synthetic_dataset(num_test_samples)
    
    y_true = test_df["recovered"].values
    y_pred = []
    y_scores = []
    
    for idx, row in test_df.iterrows():
        tx_data = {
            "bank": row["bank"],
            "payment_method": row["payment_method"],
            "error_code": row["error_code"],
            "customer_tier": row["customer_tier"],
            "amount": row["amount"],
            "hour_of_day": row["hour_of_day"],
            "day_of_month": row["day_of_month"],
            "retry_count": row["retry_count"]
        }
        res = engine.predict_recovery_propensity(tx_data)
        p_rec = res["p_recovery"]
        y_scores.append(p_rec)
        # Predict recovery if propensity > 0.50
        y_pred.append(1 if p_rec >= 0.50 else 0)

    y_pred = np.array(y_pred)
    
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    total_volume = test_df["amount"].sum()
    recovered_volume = test_df[test_df["recovered"] == 1]["amount"].sum()
    recovery_rate = (recovered_volume / total_volume) * 100.0 if total_volume > 0 else 0.0

    metrics = {
        "total_test_transactions": num_test_samples,
        "total_failed_volume_inr": round(float(total_volume), 2),
        "recovered_revenue_inr": round(float(recovered_volume), 2),
        "recovery_rate_pct": round(float(recovery_rate), 2),
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "false_positives_count": int(fp),
        "false_negatives_count": int(fn),
        "true_positives_count": int(tp),
        "true_negatives_count": int(tn)
    }
    
    print("\n================ REAL ML EVALUATION METRICS ================")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print("===========================================================\n")
    
    with open("eval_results.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    return metrics

if __name__ == "__main__":
    evaluate_real_ml_performance(100)
