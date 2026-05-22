"""
Anomaly Detection API
"""

import logging
import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException

from app.core.session_store import get_session
from app.ml.anomaly_detector import run_anomaly_detection

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/anomalies/{session_id}")
async def get_anomalies(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    df = session.get("cleaned_df")
    if df is None:
        df = session.get("df")
    if df is None:
        raise HTTPException(400, "No data in session")

    if "amount_inr" not in df.columns:
        amount_cols = [c for c in df.columns if "amount" in c.lower() or "spend" in c.lower()]
        if amount_cols:
            df["amount_inr"] = pd.to_numeric(df[amount_cols[0]], errors="coerce").fillna(0)
        else:
            return {"anomalies": [], "anomaly_count": 0}

    result = run_anomaly_detection(df)

    return result
