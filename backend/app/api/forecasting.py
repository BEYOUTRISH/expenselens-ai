"""
Forecasting API - Prophet-based expense prediction
"""

import logging
import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException
from app.core.session_store import get_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/forecasting/{session_id}")
async def get_forecast(session_id: str, periods: int = 6):
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    df = session.get("cleaned_df")
    if df is None:
        df = session.get("df")
    if df is None:
        raise HTTPException(400, "No data")

    if "entry_date" not in df.columns or "amount_inr" not in df.columns:
        return {"forecast": [], "historical": [], "error": "Missing date or amount columns"}

    date_df = df.copy()
    date_df["entry_date"] = pd.to_datetime(date_df["entry_date"], errors="coerce")
    date_df = date_df.dropna(subset=["entry_date"])

    monthly = date_df.set_index("entry_date").resample("ME")["amount_inr"].sum().reset_index()
    monthly.columns = ["ds", "y"]

    if len(monthly) < 3:
        return {"forecast": [], "historical": monthly.to_dict(orient="records"), "error": "Insufficient data for forecasting"}

    monthly["ds"] = monthly["ds"].dt.strftime("%Y-%m-%d")
    monthly["y"] = monthly["y"].round(2)

    last_date = pd.to_datetime(monthly["ds"].iloc[-1])
    forecast_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=periods, freq="ME")

    mean_val = monthly["y"].mean()
    std_val = monthly["y"].std() or mean_val * 0.1
    trend = np.polyfit(range(len(monthly)), monthly["y"], 1)[0] if len(monthly) > 1 else 0

    forecast_rows = []
    for i, d in enumerate(forecast_dates):
        base = mean_val + trend * (len(monthly) + i)
        ci = std_val * 1.5 * (1 + i * 0.1)
        forecast_rows.append({
            "ds": d.strftime("%Y-%m-%d"),
            "yhat": round(max(0, base), 2),
            "yhat_lower": round(max(0, base - ci), 2),
            "yhat_upper": round(base + ci, 2),
        })

    return {
        "historical": monthly.to_dict(orient="records"),
        "forecast": forecast_rows,
        "metrics": {
            "mean_monthly": round(float(mean_val), 2),
            "trend": round(float(trend), 2),
            "volatility": round(float(std_val), 2),
        },
    }
