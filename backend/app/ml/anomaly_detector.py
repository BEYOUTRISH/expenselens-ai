"""
Anomaly Detection Module - Isolation Forest + Z-score + Rule-based
"""

import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.core.constants import RuntimeSettings, ThresholdConfig, AnomalyWeights

logger = logging.getLogger(__name__)


def run_anomaly_detection(df: pd.DataFrame) -> dict:
    amount_col = "amount_inr" if "amount_inr" in df.columns else (
        "amount_raw_value" if "amount_raw_value" in df.columns else None
    )

    if amount_col is None:
        return {"anomalies": [], "anomaly_count": 0, "methods_used": []}

    zscore_threshold = RuntimeSettings.get_anomaly_zscore_threshold()
    iqr_multiplier = ThresholdConfig.ANOMALY_IQR_MULTIPLIER
    contamination = ThresholdConfig.ISOLATION_FOREST_CONTAMINATION
    round_modulus = ThresholdConfig.ROUND_NUMBER_MODULUS
    round_min = ThresholdConfig.ROUND_NUMBER_MIN_AMOUNT

    amounts = pd.to_numeric(df[amount_col], errors="coerce").fillna(0).values.reshape(-1, 1)
    results = df.copy()
    results["_anomaly_score"] = 0.0
    results["_anomaly_reasons"] = ""
    results["_risk_label"] = "LOW"

    # Method 1: Z-score
    mean = np.mean(amounts)
    std = np.std(amounts)
    z_scores = np.abs((amounts - mean) / std) if std > 0 else np.zeros_like(amounts)
    z_anomalies = z_scores.flatten() > zscore_threshold

    # Method 2: IQR
    q1, q3 = np.percentile(amounts, 25), np.percentile(amounts, 75)
    iqr = q3 - q1
    lower_bound = q1 - iqr_multiplier * iqr
    upper_bound = q3 + iqr_multiplier * iqr
    iqr_anomalies = (amounts.flatten() < lower_bound) | (amounts.flatten() > upper_bound)

    # Method 3: Isolation Forest
    if len(amounts) >= 10:
        iso = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
        preds = iso.fit_predict(amounts)
        iso_anomalies = preds == -1
        iso_scores = iso.score_samples(amounts)
    else:
        iso_anomalies = np.zeros(len(amounts), dtype=bool)
        iso_scores = np.zeros(len(amounts))

    # Method 4: Round-number detection
    round_anomalies = np.array([
        float(amt) % round_modulus == 0 and float(amt) > round_min
        for amt in amounts.flatten()
    ])

    # Method 5: Weekend detection
    weekend_anomalies = np.zeros(len(df), dtype=bool)
    if "entry_date" in df.columns:
        dates = pd.to_datetime(df["entry_date"], errors="coerce")
        weekend_anomalies = dates.dt.weekday.isin([5, 6]).values

    # Combine
    anomaly_list = []
    for i in range(len(df)):
        reasons = []
        score = 0.0

        z_val = float(z_scores.flatten()[i])
        if z_anomalies[i]:
            reasons.append(f"Z-score {z_val:.1f}σ above mean (threshold: {zscore_threshold:.1f}σ)")
            score += AnomalyWeights.ZSCORE

        if iqr_anomalies[i]:
            q1_v = float(q1)
            q3_v = float(q3)
            amt = float(amounts.flatten()[i])
            direction = "above" if amt > q3_v else "below"
            reasons.append(f"Outside IQR range [{q1_v:,.2f}, {q3_v:,.2f}] — {direction} Q3/Q1")
            score += AnomalyWeights.IQR

        if iso_anomalies[i]:
            iso_score = float(iso_scores[i])
            reasons.append(f"Isolation Forest anomaly score: {iso_score:.4f}")
            score += AnomalyWeights.ISOLATION_FOREST

        if round_anomalies[i]:
            reasons.append(f"Suspicious round number: ₹{float(amounts.flatten()[i]):,.2f}")
            score += AnomalyWeights.ROUND_NUMBER

        if weekend_anomalies[i]:
            reasons.append("Weekend transaction — potential policy violation")
            score += AnomalyWeights.WEEKEND

        if score > 0:
            risk = "CRITICAL" if score > 0.7 else ("HIGH" if score > 0.4 else "MEDIUM")
            row = df.iloc[i].to_dict()
            anomaly_list.append({
                "txn_ref": row.get("txn_ref", f"ROW-{i}"),
                "amount_inr": float(row.get(amount_col, 0)),
                "vendor": row.get("vendor_canonical", row.get("vendor_raw", "")),
                "department": row.get("department", ""),
                "submitted_by": row.get("submitted_by", ""),
                "entry_date": str(row.get("entry_date", "")),
                "description": str(row.get("description", ""))[:100],
                "anomaly_score": round(score, 3),
                "risk_label": risk,
                "reasons": reasons,
            })

    anomaly_list.sort(key=lambda x: x["anomaly_score"], reverse=True)

    zscore_threshold = RuntimeSettings.get_anomaly_zscore_threshold()
    return {
        "anomalies": anomaly_list[:100],
        "anomaly_count": len(anomaly_list),
        "methods_used": [
            f"Z-score > {zscore_threshold}σ",
            "IQR outlier",
            "Isolation Forest",
            "Round-number detection",
            "Weekend detection"
        ],
        "zscore_threshold": zscore_threshold,
        "iqr_bounds": {"q1": round(float(q1), 2), "q3": round(float(q3), 2), "lower": round(float(lower_bound), 2), "upper": round(float(upper_bound), 2)},
    }
