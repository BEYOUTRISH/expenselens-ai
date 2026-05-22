"""
Forecasting Engine - Prophet wrapper
"""

import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def run_forecast(df: pd.DataFrame, periods: int = 6) -> dict:
    try:
        from prophet import Prophet
        has_prophet = True
    except ImportError:
        has_prophet = False
        logger.warning("Prophet not installed, using statistical fallback")

    if "entry_date" not in df.columns or "amount_inr" not in df.columns:
        return {"error": "Missing required columns"}

    ts = df.copy()
    ts["ds"] = pd.to_datetime(ts["entry_date"], errors="coerce")
    ts = ts.dropna(subset=["ds"])
    ts["y"] = pd.to_numeric(ts["amount_inr"], errors="coerce").fillna(0)

    monthly = ts.set_index("ds").resample("ME")["y"].sum().reset_index()

    if len(monthly) < 2:
        return {"error": "Insufficient data for forecasting (need >= 2 months)"}

    if has_prophet:
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        model.fit(monthly)
        future = model.make_future_dataframe(periods=periods, freq="ME")
        forecast = model.predict(future)

        result = {
            "historical": monthly.to_dict(orient="records"),
            "forecast": forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods).to_dict(orient="records"),
            "components": {
                "trend": forecast[["ds", "trend"]].to_dict(orient="records"),
                "weekly": forecast[["ds", "weekly"]].to_dict(orient="records"),
                "yearly": forecast[["ds", "yearly"]].to_dict(orient="records"),
            },
            "method": "prophet",
        }
    else:
        mean_val = monthly["y"].mean()
        std_val = monthly["y"].std()
        last_date = monthly["ds"].max()
        forecast_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=periods, freq="ME")
        trend_coef = np.polyfit(range(len(monthly)), monthly["y"], 1)[0] if len(monthly) > 1 else 0

        forecast_rows = []
        for i, d in enumerate(forecast_dates):
            base = mean_val + trend_coef * (len(monthly) + i)
            ci = std_val * 1.96 * (1 + i * 0.1)
            forecast_rows.append({
                "ds": d,
                "yhat": max(0, base),
                "yhat_lower": max(0, base - ci),
                "yhat_upper": base + ci,
            })

        result = {
            "historical": monthly.to_dict(orient="records"),
            "forecast": forecast_rows,
            "method": "statistical_fallback",
        }

    for series in ["historical", "forecast"]:
        for row in result.get(series, []):
            for col in ["y", "yhat", "yhat_lower", "yhat_upper", "trend"]:
                if col in row and isinstance(row[col], (np.integer, np.floating)):
                    row[col] = round(float(row[col]), 2)
                if col in row and hasattr(row[col], "strftime"):
                    row[col] = row[col].strftime("%Y-%m-%d")

    return result
