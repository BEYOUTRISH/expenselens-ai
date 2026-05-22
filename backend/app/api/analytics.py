"""
Analytics API - All dashboard data endpoints
"""

import logging
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from app.core.session_store import get_session
from app.core.constants import compute_compliance_score, RuntimeSettings, ThresholdConfig

logger = logging.getLogger(__name__)
router = APIRouter()


def _normalize_receipt_val(val):
    import pandas as pd
    if pd.isna(val):
        return False
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in ("yes", "true", "1", "y", "t")


def get_df(session_id: str):
    import pandas as pd
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    df = session.get("cleaned_df")
    is_cleaned = df is not None
    if df is None:
        df = session.get("df")
    if df is None:
        raise HTTPException(400, "No data")
    
    if not is_cleaned:
        df = df.copy()
        if "entry_date" not in df.columns and "txn_date" in df.columns:
            df["entry_date"] = df["txn_date"]
        if "amount_inr" not in df.columns:
            for alt_col in ["amount_raw_value", "amount", "total", "spend"]:
                if alt_col in df.columns:
                    df["amount_inr"] = pd.to_numeric(df[alt_col], errors="coerce").fillna(0)
                    break
        if "receipt_attached" in df.columns:
            col_dtype = df["receipt_attached"].dtype
            if col_dtype == object:
                df["receipt_attached"] = df["receipt_attached"].apply(_normalize_receipt_val)
    
    return df


@router.get("/analytics/summary/{session_id}")
async def get_summary(session_id: str):
    df = get_df(session_id)
    numeric_cols = [c for c in ["amount_inr", "amount_raw_value"] if c in df.columns]
    amount_col = numeric_cols[0] if numeric_cols else None

    if amount_col:
        total_spend = float(df[amount_col].sum())
        avg_txn = float(df[amount_col].mean())
        max_txn = float(df[amount_col].max())
        min_txn = float(df[amount_col].min())
    else:
        total_spend = avg_txn = max_txn = min_txn = 0

    anomaly_count = int(df["is_flagged"].sum()) if "is_flagged" in df.columns else 0
    duplicate_count = int(df["is_duplicate"].sum()) if "is_duplicate" in df.columns else 0
    personal_count = int(df["is_personal"].sum()) if "is_personal" in df.columns else 0
    no_receipt = int((df["receipt_attached"] == False).sum()) if "receipt_attached" in df.columns else 0

    compliance_result = compute_compliance_score(df)
    compliance_score = int(compliance_result["score"])

    return {
        "total_spend": round(total_spend, 2),
        "transaction_count": len(df),
        "average_transaction": round(avg_txn, 2),
        "max_transaction": round(max_txn, 2),
        "min_transaction": round(min_txn, 2),
        "anomaly_count": anomaly_count,
        "duplicate_count": duplicate_count,
        "personal_count": personal_count,
        "no_receipt_count": no_receipt,
        "compliance_score": compliance_score,
        "compliance_breakdown": compliance_result["breakdown"],
    }


@router.get("/analytics/departments/{session_id}")
async def get_departments(session_id: str):
    df = get_df(session_id)
    if "department" not in df.columns or "amount_inr" not in df.columns:
        return []

    def _dept_agg(group: pd.DataFrame):
        amount = group["amount_inr"]
        positive_mask = amount > 0
        negative_mask = amount < 0
        zero_mask = amount == 0

        return pd.Series({
            "total_spend": amount.sum(),
            "transaction_count": len(group),
            "avg_spend": amount.mean(),
            "positive_count": positive_mask.sum(),
            "negative_count": negative_mask.sum(),
            "zero_count": zero_mask.sum(),
            "total_positive_value": amount[positive_mask].sum() if positive_mask.any() else 0,
            "total_negative_value": (-amount[negative_mask]).sum() if negative_mask.any() else 0,
        })

    df = df.copy()
    df["department"] = df["department"].fillna("Unknown")
    df["department"] = df["department"].astype(str).apply(
        lambda x: "Unknown" if not x.strip() else x
    )

    dept_group = df.groupby("department", dropna=False).apply(_dept_agg).reset_index()
    dept_group["total_spend"] = dept_group["total_spend"].round(2)
    dept_group["avg_spend"] = dept_group["avg_spend"].round(2)
    dept_group["total_positive_value"] = dept_group["total_positive_value"].round(2)
    dept_group["total_negative_value"] = dept_group["total_negative_value"].round(2)
    dept_group = dept_group.fillna(0)
    return dept_group.sort_values("total_spend", ascending=False).to_dict(orient="records")


@router.get("/analytics/vendors/{session_id}")
async def get_vendors(session_id: str, top_n: int = Query(20, le=100)):
    df = get_df(session_id)
    vendor_col = "vendor_canonical" if "vendor_canonical" in df.columns else "vendor_raw"

    if vendor_col not in df.columns or "amount_inr" not in df.columns:
        return []

    vendor_group = df.groupby(vendor_col).agg(
        total_spend=("amount_inr", "sum"),
        transaction_count=("amount_inr", "count"),
        avg_spend=("amount_inr", "mean"),
    ).reset_index()
    vendor_group["total_spend"] = vendor_group["total_spend"].round(2)
    vendor_group["avg_spend"] = vendor_group["avg_spend"].round(2)
    return vendor_group.sort_values("total_spend", ascending=False).head(top_n).to_dict(orient="records")


@router.get("/analytics/employees/{session_id}")
async def get_employees(session_id: str):
    df = get_df(session_id)
    if "submitted_by" not in df.columns or "amount_inr" not in df.columns:
        return []

    df = df.copy()
    df["submitted_by"] = df["submitted_by"].fillna("Unknown")
    df["submitted_by"] = df["submitted_by"].astype(str).apply(
        lambda x: "Unknown" if not x.strip() else x
    )

    emp_group = df.groupby("submitted_by").agg(
        total_spend=("amount_inr", "sum"),
        transaction_count=("amount_inr", "count"),
        avg_spend=("amount_inr", "mean"),
    ).reset_index()
    emp_group["total_spend"] = emp_group["total_spend"].round(2)
    emp_group["avg_spend"] = emp_group["avg_spend"].round(2)
    return emp_group.sort_values("total_spend", ascending=False).to_dict(orient="records")


@router.get("/analytics/timeline/{session_id}")
async def get_timeline(session_id: str):
    df = get_df(session_id)
    if "entry_date" not in df.columns:
        return []

    date_df = df.copy()
    date_df["entry_date"] = pd.to_datetime(date_df["entry_date"], errors="coerce")
    date_df = date_df.dropna(subset=["entry_date"])

    if "amount_inr" in date_df.columns:
        daily = date_df.groupby(date_df["entry_date"].dt.strftime("%Y-%m-%d")).agg(
            total_spend=("amount_inr", "sum"),
            count=("amount_inr", "count"),
        ).reset_index()
        daily.columns = ["date", "total_spend", "count"]
        daily["total_spend"] = daily["total_spend"].round(2)
        return daily.sort_values("date").to_dict(orient="records")
    return []


@router.get("/analytics/compliance/{session_id}")
async def get_compliance(session_id: str):
    df = get_df(session_id)
    
    compliance_result = compute_compliance_score(df)
    
    result = {
        "overall_compliance_score": compliance_result["score"],
        "compliance_breakdown": compliance_result["breakdown"],
        "receipt_compliance_rate": 100,
        "missing_receipts_count": 0,
        "high_value_without_receipt": [],
        "policy_violations": [],
    }

    if "receipt_attached" in df.columns:
        total = len(df)
        missing = int((df["receipt_attached"] == False).sum()) if total > 0 else 0
        result["missing_receipts_count"] = missing
        result["receipt_compliance_rate"] = round((total - missing) / total * 100, 2) if total > 0 else 100

    if "amount_inr" in df.columns and "receipt_attached" in df.columns:
        threshold = RuntimeSettings.get_receipt_threshold()
        high_no_receipt = df[(df["amount_inr"] > threshold) & (df["receipt_attached"] == False)]
        result["high_value_without_receipt"] = high_no_receipt.head(20).to_dict(orient="records")
        result["receipt_threshold"] = threshold

    flagged = df[df["is_flagged"] == True] if "is_flagged" in df.columns else []
    result["policy_violations"] = flagged.head(20).to_dict(orient="records")

    return result
