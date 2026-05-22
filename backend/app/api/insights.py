"""
AI Insights API - Generate financial analyst narrative reports
"""

import logging
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.session_store import get_session
from app.core.constants import compute_compliance_score, RuntimeSettings
from app.services.ai_service import generate_ai_insights
from app.core.constants import (
    compute_compliance_score, compute_employee_compliance, RuntimeSettings, ThresholdConfig,
    PERSONAL_KEYWORD_CATEGORIES, PERSONAL_CATEGORY_RISKS, PERSONAL_CATEGORY_SOLUTIONS,
    PERSONAL_EXPENSE_OVERALL_RISKS, PERSONAL_EXPENSE_OVERALL_SOLUTIONS,
    PERSONAL_KEYWORD_WEIGHTS, create_word_boundary_pattern
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _normalize_df_for_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DataFrame for analysis - handles raw vs cleaned data differences.
    - Converts string dates to datetime
    - Normalizes receipt_attached (string -> boolean)
    - Creates entry_date from txn_date if needed
    - Creates txn_ref from txn_id if needed
    - Creates amount_inr from amount if needed
    """
    result = df.copy()
    
    if "entry_date" not in result.columns and "txn_date" in result.columns:
        result["entry_date"] = result["txn_date"]
        logger.info("Created entry_date from txn_date")
    
    if "txn_ref" not in result.columns:
        if "txn_id" in result.columns:
            result["txn_ref"] = result["txn_id"].astype(str)
        else:
            result["txn_ref"] = [f"ROW-{i:06d}" for i in range(len(result))]
        logger.info("Created txn_ref column")
    
    if "amount_inr" not in result.columns:
        for alt_col in ["amount_raw_value", "amount", "total", "spend"]:
            if alt_col in result.columns:
                result["amount_inr"] = pd.to_numeric(result[alt_col], errors="coerce").fillna(0)
                logger.info(f"Created amount_inr from {alt_col}")
                break
    
    if "receipt_attached" in result.columns:
        col = result["receipt_attached"]
        if col.dtype == object or col.dtype == str:
            def _normalize_receipt(val):
                if pd.isna(val):
                    return False
                if isinstance(val, bool):
                    return val
                s = str(val).strip().lower()
                return s in ("yes", "true", "1", "y", "t")
            result["receipt_attached"] = result["receipt_attached"].apply(_normalize_receipt)
            logger.info("Normalized receipt_attached from string to boolean")
    
    if "vendor_canonical" not in result.columns and "vendor_raw" in result.columns:
        result["vendor_canonical"] = result["vendor_raw"]
    elif "vendor_canonical" not in result.columns and "vendor" in result.columns:
        result["vendor_canonical"] = result["vendor"]
    
    return result


def _generate_rule_based_insights(df, summary: dict) -> dict:
    insights = {
        "executive_summary": "",
        "spending_patterns": [],
        "vendor_analysis": [],
        "department_trends": [],
        "anomaly_insights": [],
        "recommendations": [],
        "risk_signals": [],
        "employee_analysis": [],
        "vendor_risk": {},
        "time_patterns": {},
        "receipt_compliance": {},
        "duplicate_analysis": {},
        "high_value_transactions": {},
    }

    total = summary.get("total_spend", 0)
    count = summary.get("transaction_count", 0)
    anomalies = summary.get("anomaly_count", 0)
    compliance = summary.get("compliance_score", 100)
    personal = summary.get("personal_count", 0)
    amount_col = "amount_inr" if "amount_inr" in df.columns else (
        "amount_raw_value" if "amount_raw_value" in df.columns else None
    )

    insights["executive_summary"] = (
        f"Total expenditure for the period is ₹{total:,.2f} across {count} transactions. "
        f"The compliance score is {compliance}%, with {anomalies} flagged anomalies "
        f"and {personal} personal expenses detected. "
        f"{'Overall financial discipline appears strong.' if compliance > 80 else 'Several compliance gaps require attention.'}"
    )

    if "department" in df.columns and amount_col:
        dept_totals = df.groupby("department")[amount_col].sum().sort_values(ascending=False)
        for dept, amt in dept_totals.head(5).items():
            pct = (amt / total * 100) if total else 0
            insights["department_trends"].append({
                "department": dept,
                "total_spend": round(float(amt), 2),
                "percentage": round(float(pct), 1),
            })

        if len(dept_totals) >= 2:
            top_dept = dept_totals.index[0]
            top_amt = dept_totals.iloc[0]
            insights["spending_patterns"].append(
                f"{top_dept} accounts for the highest spend at ₹{top_amt:,.2f}, "
                f"representing {top_amt/total*100:.1f}% of total expenditure."
            )

    if "vendor_canonical" in df.columns and amount_col:
        vendor_totals = df.groupby("vendor_canonical")[amount_col].sum().sort_values(ascending=False)
        top_vendor = vendor_totals.index[0] if len(vendor_totals) > 0 else "N/A"
        top_vendor_amt = float(vendor_totals.iloc[0]) if len(vendor_totals) > 0 else 0
        vendor_pct = (top_vendor_amt / total * 100) if total else 0

        if vendor_pct > 20:
            insights["risk_signals"].append(
                f"HIGH VENDOR CONCENTRATION: {top_vendor} represents {vendor_pct:.1f}% of total spend "
                f"(₹{top_vendor_amt:,.2f}). Consider diversifying to reduce dependency risk."
            )

        insights["vendor_analysis"].append({
            "top_vendor": top_vendor,
            "top_vendor_spend": round(top_vendor_amt, 2),
            "top_vendor_pct": round(vendor_pct, 1),
            "unique_vendors": int(vendor_totals.count()),
        })

    if anomalies > 0:
        insights["anomaly_insights"].append(
            f"{anomalies} suspicious transactions detected requiring review. "
            f"This represents {anomalies/count*100:.1f}% of all transactions."
        )

    if personal > 0:
        insights["risk_signals"].append(
            f"{personal} personal expenses submitted as corporate expenses totalling approximately "
            f"₹{df[df['is_personal']==True][amount_col].sum():,.2f}. Policy reinforcement recommended."
        )

    if compliance < 70:
        insights["recommendations"].append(
            "Implement mandatory receipt upload policy for all transactions above ₹5,000."
        )
    insights["recommendations"].append(
        "Schedule monthly expense audit reviews to catch anomalies early."
    )

    # === NEW: Employee Analysis ===
    if "submitted_by" in df.columns and amount_col:
        emp_df = df.copy()
        emp_df["submitted_by"] = emp_df["submitted_by"].fillna("Unknown")
        emp_df["submitted_by"] = emp_df["submitted_by"].astype(str).apply(
            lambda x: "Unknown" if not x.strip() else x
        )

        emp_stats = emp_df.groupby("submitted_by").agg(
            total_spend=(amount_col, "sum"),
            transaction_count=(amount_col, "count"),
            avg_spend=(amount_col, "mean"),
        ).reset_index()
        emp_stats = emp_stats.sort_values("total_spend", ascending=False)

        for _, row in emp_stats.head(10).iterrows():
            emp_compliance = compute_employee_compliance(emp_df, row["submitted_by"])

            insights["employee_analysis"].append({
                "submitted_by": row["submitted_by"],
                "total_spend": round(float(row["total_spend"]), 2),
                "transaction_count": int(row["transaction_count"]),
                "avg_spend": round(float(row["avg_spend"]), 2),
                "compliance_rate": emp_compliance,
            })

    # === NEW: Vendor Risk Analysis ===
    if "vendor_canonical" in df.columns and amount_col:
        vendor_stats = df.groupby("vendor_canonical").agg(
            total_spend=(amount_col, "sum"),
            transaction_count=(amount_col, "count"),
        ).reset_index()
        vendor_stats["spend_pct"] = (vendor_stats["total_spend"] / total * 100) if total > 0 else 0

        high_concentration = vendor_stats[vendor_stats["spend_pct"] > 10].sort_values("spend_pct", ascending=False)
        insights["vendor_risk"]["high_concentration_vendors"] = [
            {"vendor": r["vendor_canonical"], "spend_pct": round(float(r["spend_pct"]), 1), "total_spend": round(float(r["total_spend"]), 2)}
            for _, r in high_concentration.head(5).iterrows()
        ]

        if "is_flagged" in df.columns:
            vendor_anomalies = df[df["is_flagged"] == True].groupby("vendor_canonical").size().reset_index(name="anomaly_count")
            vendor_anomalies = vendor_anomalies.sort_values("anomaly_count", ascending=False)
            insights["vendor_risk"]["vendors_with_anomalies"] = [
                {"vendor": r["vendor_canonical"], "anomaly_count": int(r["anomaly_count"])}
                for _, r in vendor_anomalies.head(5).iterrows()
            ]

        unique_vendors = vendor_stats["vendor_canonical"].nunique()
        top_3_share = vendor_stats.nlargest(3, "total_spend")["total_spend"].sum() / total * 100 if total > 0 else 0
        insights["vendor_risk"]["vendor_diversity_score"] = round(min(100, max(0, 100 - top_3_share + (unique_vendors / 10))), 1)

    # === NEW: Time-Based Patterns ===
    if "entry_date" in df.columns and amount_col:
        date_df = df.copy()
        date_df["entry_date"] = pd.to_datetime(date_df["entry_date"], errors="coerce")
        date_df = date_df.dropna(subset=["entry_date"])

        if len(date_df) > 0:
            DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            
            date_df["day_of_week_idx"] = date_df["entry_date"].dt.dayofweek
            
            day_stats = date_df.groupby("day_of_week_idx").agg(
                total_spend=(amount_col, "sum"),
                count=(amount_col, "count"),
            ).reset_index()
            
            day_stats_dict = {int(r["day_of_week_idx"]): {"total_spend": r["total_spend"], "count": r["count"]} 
                            for _, r in day_stats.iterrows()}
            
            insights["time_patterns"]["day_of_week_patterns"] = []
            for idx, day in enumerate(DAY_NAMES):
                stats = day_stats_dict.get(idx, {"total_spend": 0, "count": 0})
                insights["time_patterns"]["day_of_week_patterns"].append({
                    "day": day,
                    "total_spend": round(float(stats["total_spend"]), 2),
                    "count": int(stats["count"])
                })

            date_df["month"] = date_df["entry_date"].dt.to_period("M")
            monthly = date_df.groupby("month")[amount_col].sum()
            if len(monthly) > 1:
                busiest = monthly.idxmax()
                quietest = monthly.idxmin()
                insights["time_patterns"]["busiest_month"] = str(busiest)
                insights["time_patterns"]["quietest_month"] = str(quietest)

                month_end = date_df[date_df["entry_date"].dt.day >= 25]
                month_start = date_df[date_df["entry_date"].dt.day <= 5]
                month_end_spike = len(month_end) > len(month_start) * 1.5
                insights["time_patterns"]["month_end_spike"] = month_end_spike
                if month_end_spike:
                    insights["spending_patterns"].append(
                        f"Significant month-end spending detected: {len(month_end)} transactions in the last week of each month vs {len(month_start)} in the first week."
                    )

    # === NEW: Receipt Compliance ===
    if "receipt_attached" in df.columns:
        total_rows = len(df)
        with_receipt = int(df["receipt_attached"].sum())
        overall_rate = round(with_receipt / total_rows * 100, 1) if total_rows > 0 else 0

        insights["receipt_compliance"]["overall_rate"] = overall_rate

        if "department" in df.columns:
            dept_receipt = df.groupby("department").agg(
                total=("receipt_attached", "count"),
                with_receipt=("receipt_attached", "sum"),
            ).reset_index()
            dept_receipt["rate"] = (dept_receipt["with_receipt"] / dept_receipt["total"] * 100).round(1)
            insights["receipt_compliance"]["by_department"] = [
                {"department": r["department"], "rate": round(float(r["rate"]), 1), "with_receipt": int(r["with_receipt"]), "total": int(r["total"])}
                for _, r in dept_receipt.iterrows()
            ]

        if amount_col:
            threshold = RuntimeSettings.get_receipt_threshold()
            high_no_receipt = df[(df[amount_col] > threshold) & (df["receipt_attached"] == False)]
            insights["receipt_compliance"]["high_value_missing_receipt"] = [
                {"txn_ref": r.get("txn_ref", ""), "amount": round(float(r[amount_col]), 2), "vendor": r.get("vendor_canonical", r.get("vendor_raw", "")), "department": r.get("department", "")}
                for _, r in high_no_receipt.head(10).iterrows()
            ]

    # === NEW: Duplicate Analysis ===
    if "is_duplicate" in df.columns:
        confirmed_dups = df[df["is_duplicate"] == True]
        dup_count = len(confirmed_dups)
        dup_value = float(confirmed_dups[amount_col].sum()) if amount_col and dup_count > 0 else 0

        insights["duplicate_analysis"]["confirmed_duplicates"] = dup_count
        insights["duplicate_analysis"]["duplicate_value"] = round(dup_value, 2)

        potential_dups = 0
        if amount_col and "entry_date" in df.columns:
            date_df = df.copy()
            date_df["entry_date"] = pd.to_datetime(date_df["entry_date"], errors="coerce")
            date_df = date_df.dropna(subset=["entry_date"])
            date_df["date_amount_key"] = date_df["entry_date"].dt.strftime("%Y-%m-%d") + "_" + date_df[amount_col].astype(str)
            dup_groups = date_df["date_amount_key"].value_counts()
            potential_dups = int((dup_groups > 1).sum())

        insights["duplicate_analysis"]["potential_duplicates"] = potential_dups

        if dup_count > 0:
            insights["spending_patterns"].append(
                f"{dup_count} confirmed duplicate transactions worth ₹{dup_value:,.2f} detected. "
                f"Review and remove to avoid double-counting."
            )

    # === NEW: High-Value Transactions ===
    if amount_col:
        threshold = df[amount_col].quantile(0.99)
        high_value = df[df[amount_col] >= threshold].sort_values(amount_col, ascending=False)

        def _safe_str(val) -> str:
            if pd.isna(val):
                return "Unknown"
            s = str(val).strip()
            return s if s else "Unknown"

        insights["high_value_transactions"]["top_1_percent"] = [
            {
                "txn_ref": r.get("txn_ref", ""),
                "amount": round(float(r[amount_col]), 2),
                "vendor": r.get("vendor_canonical", r.get("vendor_raw", "")),
                "department": _safe_str(r.get("department", "")),
                "submitted_by": _safe_str(r.get("submitted_by", "")),
                "is_flagged": bool(r.get("is_flagged", False)),
            }
            for _, r in high_value.head(10).iterrows()
        ]
        insights["high_value_transactions"]["threshold"] = round(float(threshold), 2)
        insights["high_value_transactions"]["total_high_value"] = round(float(high_value[amount_col].sum()), 2)
        insights["high_value_transactions"]["count"] = len(high_value)

        if len(high_value) > 0:
            insights["risk_signals"].append(
                f"Top 1% of transactions (≥ ₹{threshold:,.2f}) account for ₹{high_value[amount_col].sum():,.2f} "
                f"across {len(high_value)} transactions. Enhanced scrutiny recommended for these high-value entries."
            )

    if personal > 0 and "is_personal" in df.columns and amount_col:
        personal_df = df[df["is_personal"] == True].copy()

        def _safe_str_personal(val) -> str:
            if pd.isna(val):
                return "Unknown"
            s = str(val).strip()
            return s if s else "Unknown"

        if "submitted_by" in personal_df.columns:
            personal_df["submitted_by"] = personal_df["submitted_by"].apply(_safe_str_personal)
        if "department" in personal_df.columns:
            personal_df["department"] = personal_df["department"].apply(_safe_str_personal)

        insights["personal_expense_analysis"] = {
            "total_count": int(personal),
            "total_value": round(float(personal_df[amount_col].sum()), 2),
            "percentage_of_total": round(personal / count * 100, 1) if count > 0 else 0,
        }

        if "description" in personal_df.columns:
            category_counts: dict[str, int] = {}
            category_values: dict[str, float] = {}
            keyword_counts: dict[str, int] = {}
            keyword_values: dict[str, float] = {}

            for kw, cat in PERSONAL_KEYWORD_CATEGORIES.items():
                pattern = create_word_boundary_pattern(kw)
                mask = personal_df["description"].astype(str).str.contains(pattern, na=False)
                kw_count = int(mask.sum())
                if kw_count > 0:
                    kw_value = float(personal_df[mask][amount_col].sum()) if amount_col else 0
                    keyword_counts[kw] = kw_count
                    keyword_values[kw] = kw_value

                    category_counts[cat] = category_counts.get(cat, 0) + kw_count
                    category_values[cat] = category_values.get(cat, 0) + kw_value

            insights["personal_expense_analysis"]["by_category"] = [
                {
                    "category": cat,
                    "count": category_counts.get(cat, 0),
                    "value": round(category_values.get(cat, 0), 2),
                    "risk_outcomes": PERSONAL_CATEGORY_RISKS.get(cat, []),
                    "recommended_actions": PERSONAL_CATEGORY_SOLUTIONS.get(cat, []),
                }
                for cat in sorted(category_counts.keys(), key=lambda c: category_counts[c], reverse=True)
            ]

            sorted_keywords = sorted(
                keyword_counts.keys(),
                key=lambda k: keyword_counts[k],
                reverse=True
            )
            insights["personal_expense_analysis"]["top_keywords"] = [
                {
                    "keyword": kw,
                    "count": keyword_counts[kw],
                    "value": round(keyword_values[kw], 2),
                    "category": PERSONAL_KEYWORD_CATEGORIES.get(kw, "Uncategorized"),
                }
                for kw in sorted_keywords[:10]
            ]

        if "submitted_by" in personal_df.columns and amount_col:
            emp_personal = personal_df.groupby("submitted_by").agg(
                count=(amount_col, "count"),
                value=(amount_col, "sum"),
            ).reset_index()
            emp_personal = emp_personal.sort_values("count", ascending=False)

            insights["personal_expense_analysis"]["by_employee"] = [
                {
                    "employee": r["submitted_by"],
                    "count": int(r["count"]),
                    "value": round(float(r["value"]), 2),
                }
                for _, r in emp_personal.head(10).iterrows()
            ]

        if "department" in personal_df.columns and amount_col:
            dept_personal = personal_df.groupby("department").agg(
                count=(amount_col, "count"),
                value=(amount_col, "sum"),
            ).reset_index()
            dept_personal = dept_personal.sort_values("count", ascending=False)

            insights["personal_expense_analysis"]["by_department"] = [
                {
                    "department": r["department"],
                    "count": int(r["count"]),
                    "value": round(float(r["value"]), 2),
                }
                for _, r in dept_personal.head(10).iterrows()
            ]

        insights["personal_expense_analysis"]["overall_risk_outcomes"] = PERSONAL_EXPENSE_OVERALL_RISKS
        insights["personal_expense_analysis"]["overall_recommended_actions"] = PERSONAL_EXPENSE_OVERALL_SOLUTIONS

    return insights


@router.post("/insights/generate/{session_id}")
async def generate_insights(
    session_id: str,
    ai_provider: Optional[str] = Query(None, description="Override AI provider: 'groq', 'none', or 'openai'"),
):
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
        logger.warning("Using raw (uncleaned) data - normalizing for analysis")
        df = _normalize_df_for_analysis(df)

    numeric_cols = [c for c in ["amount_inr", "amount_raw_value"] if c in df.columns]
    amount_col = numeric_cols[0] if numeric_cols else None

    compliance_result = compute_compliance_score(df)
    
    summary = {}
    if amount_col:
        summary["total_spend"] = float(df[amount_col].sum())
        summary["transaction_count"] = len(df)
        summary["average_transaction"] = float(df[amount_col].mean())
        summary["max_transaction"] = float(df[amount_col].max())
        summary["min_transaction"] = float(df[amount_col].min())
    summary["anomaly_count"] = int(df["is_flagged"].sum()) if "is_flagged" in df.columns else 0
    summary["duplicate_count"] = int(df["is_duplicate"].sum()) if "is_duplicate" in df.columns else 0
    summary["personal_count"] = int(df["is_personal"].sum()) if "is_personal" in df.columns else 0
    summary["compliance_score"] = compliance_result["score"]
    summary["compliance_breakdown"] = compliance_result["breakdown"]

    insights = _generate_rule_based_insights(df, summary)

    preferred_provider = ai_provider if ai_provider is not None else RuntimeSettings.get("ai_provider", "none")

    if preferred_provider == "none":
        return {
            "session_id": session_id,
            "summary": summary,
            "insights": insights,
            "ai": False,
            "ai_provider": None,
        }

    ai_insights, actual_provider = generate_ai_insights(df, summary)
    if ai_insights:
        return {
            "session_id": session_id,
            "summary": summary,
            "insights": ai_insights,
            "ai": True,
            "ai_provider": actual_provider,
        }

    return {
        "session_id": session_id,
        "summary": summary,
        "insights": insights,
        "ai": False,
        "ai_provider": None,
    }
