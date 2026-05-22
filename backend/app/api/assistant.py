"""
AI Chat Assistant API - Natural language queries over expense data
"""

import logging
import json
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.session_store import get_session
from app.services.ai_service import chat_with_ai
from app.core.constants import compute_compliance_score, RuntimeSettings

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str
    ai_provider: Optional[str] = None


@router.post("/assistant/chat")
async def chat_with_data(req: ChatRequest):
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    df = session.get("cleaned_df")
    if df is None:
        df = session.get("df")
    if df is None:
        raise HTTPException(400, "No data")

    amount_col = "amount_inr" if "amount_inr" in df.columns else (
        "amount_raw_value" if "amount_raw_value" in df.columns else None
    )
    compliance_result = compute_compliance_score(df)
    summary = {
        "total_spend": float(df[amount_col].sum()) if amount_col else 0,
        "transaction_count": len(df),
        "average_transaction": float(df[amount_col].mean()) if amount_col else 0,
        "max_transaction": float(df[amount_col].max()) if amount_col else 0,
        "min_transaction": float(df[amount_col].min()) if amount_col else 0,
        "anomaly_count": int(df["is_flagged"].sum()) if "is_flagged" in df.columns else 0,
        "duplicate_count": int(df["is_duplicate"].sum()) if "is_duplicate" in df.columns else 0,
        "personal_count": int(df["is_personal"].sum()) if "is_personal" in df.columns else 0,
        "compliance_score": compliance_result["score"],
    }

    preferred_provider = req.ai_provider if req.ai_provider is not None else RuntimeSettings.get("ai_provider", "none")

    if preferred_provider != "none":
        ai_response, actual_provider = chat_with_ai(req.session_id, req.message, df, summary)
        if ai_response:
            return {"response": ai_response, "message": req.message, "ai": True, "ai_provider": actual_provider}

    msg = req.message.lower()
    response = _rule_based_chat(msg, df)
    return {"response": response, "message": req.message, "ai": False, "ai_provider": None}


def _rule_based_chat(msg: str, df: pd.DataFrame) -> str:
    amount_col = "amount_inr" if "amount_inr" in df.columns else (
        "amount_raw_value" if "amount_raw_value" in df.columns else None
    )

    if "negative" in msg or "minus" in msg or "less than 0" in msg:
        if amount_col:
            negatives = df[df[amount_col] < 0]
            if len(negatives) == 0:
                return "No negative amounts found. All transactions have positive values."
            total = negatives[amount_col].sum()
            return (
                f"Found {len(negatives)} transactions with negative amounts "
                f"totaling ₹{total:,.2f}. "
                f"These may represent refunds, reversals, or data entry errors."
            )

    if "overspend" in msg or "overspent" in msg or "most spend" in msg:
        if "department" in df.columns and amount_col:
            dept_spend = df.groupby("department")[amount_col].sum().sort_values(ascending=False)
            top = dept_spend.head(3)
            return f"Top spending departments:\n" + "\n".join(
                [f"• {dept}: ₹{amt:,.2f}" for dept, amt in top.items()]
            )

    if "suspicious" in msg or "anomal" in msg or "flagged" in msg:
        if "is_flagged" in df.columns:
            flagged = df[df["is_flagged"] == True]
            if len(flagged) == 0:
                return "No suspicious transactions detected in the current dataset."
            count = len(flagged)
            total = flagged[amount_col].sum() if amount_col else 0
            return (
                f"Found {count} flagged transactions totaling ₹{total:,.2f}. "
                f"These include personal expenses and policy violations. "
                f"Review the Anomaly Dashboard for detailed explanations."
            )

    if "top vendor" in msg or "vendor" in msg or "supplier" in msg:
        vendor_col = "vendor_canonical" if "vendor_canonical" in df.columns else (
            "vendor_raw" if "vendor_raw" in df.columns else None
        )
        if vendor_col and amount_col:
            vendors = df.groupby(vendor_col)[amount_col].sum().sort_values(ascending=False).head(5)
            return f"Top 5 vendors by spend:\n" + "\n".join(
                [f"• {v}: ₹{a:,.2f}" for v, a in vendors.items()]
            )

    if "spike" in msg or "march" in msg or "trend" in msg:
        if "entry_date" in df.columns and amount_col:
            date_df = df.copy()
            date_df["entry_date"] = pd.to_datetime(date_df["entry_date"], errors="coerce")
            monthly = date_df.set_index("entry_date").resample("ME")[amount_col].sum()
            if len(monthly) > 1:
                pct_change = monthly.pct_change() * 100
                max_spike = pct_change.idxmax()
                return (
                    f"The largest monthly spike was in {max_spike.strftime('%B %Y')} "
                    f"with a {pct_change.max():.1f}% increase over the previous month. "
                    f"Total monthly spend ranged from ₹{monthly.min():,.2f} to ₹{monthly.max():,.2f}."
                )

    if "forecast" in msg or "predict" in msg or "next month" in msg:
        if amount_col:
            total = df[amount_col].sum()
            avg = df[amount_col].mean()
            return (
                f"Based on {len(df)} transactions totaling ₹{total:,.2f}, "
                f"the average transaction is ₹{avg:,.2f}. "
                f"Use the Forecasting page for a detailed projection with confidence intervals."
            )

    if "personal" in msg or "private" in msg:
        if "is_personal" in df.columns:
            personal = df[df["is_personal"] == True]
            if len(personal) == 0:
                return "No personal expenses detected."
            total = personal[amount_col].sum() if amount_col else 0
            return (
                f"Found {len(personal)} personal expenses totaling ₹{total:,.2f}. "
                f"These should be reimbursed or written off as non-business expenses."
            )

    if "duplicate" in msg:
        if "is_duplicate" in df.columns:
            dups = df[df["is_duplicate"] == True]
            if len(dups) == 0:
                return "No duplicate transactions detected."
            total = dups[amount_col].sum() if amount_col else 0
            return (
                f"Found {len(dups)} duplicate transactions worth ₹{total:,.2f}. "
                f"These should be removed before finalizing the ledger."
            )

    return (
        f"I can help you understand your expense data. I see {len(df)} transactions"
        + (f" totaling ₹{df[amount_col].sum():,.2f}." if amount_col else ".")
        + " Try asking: 'Which department overspent?', 'Top vendors?', 'Any anomalies?'"
    )
