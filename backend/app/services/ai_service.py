"""
AI Service - Groq integration for chat and insights generation
Fallback chain: Groq → Rule-based (None returned)
"""

import logging
import os
import json
from typing import Optional, Tuple
import pandas as pd
from dotenv import load_dotenv

from app.core.constants import compute_compliance_score

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

logger = logging.getLogger(__name__)

_groq_client = None
_groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_groq_api_key = os.getenv("GROQ_API_KEY", "")


def _get_groq_client():
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    if not _groq_api_key:
        return None
    try:
        from groq import Groq
        _groq_client = Groq(api_key=_groq_api_key)
        return _groq_client
    except ImportError:
        logger.warning("groq package not installed")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        return None


def _build_data_context(df: pd.DataFrame, summary: dict) -> str:
    amount_col = "amount_inr" if "amount_inr" in df.columns else (
        "amount_raw_value" if "amount_raw_value" in df.columns else None
    )

    context_parts = []

    context_parts.append(f"Total transactions: {summary.get('transaction_count', len(df))}")
    context_parts.append(f"Total spend: ₹{summary.get('total_spend', 0):,.2f}")
    context_parts.append(f"Average transaction: ₹{summary.get('average_transaction', 0):,.2f}")
    context_parts.append(f"Max transaction: ₹{summary.get('max_transaction', 0):,.2f}")
    context_parts.append(f"Min transaction: ₹{summary.get('min_transaction', 0):,.2f}")
    context_parts.append(f"Anomalies flagged: {summary.get('anomaly_count', 0)}")
    context_parts.append(f"Duplicate transactions: {summary.get('duplicate_count', 0)}")
    context_parts.append(f"Personal expenses: {summary.get('personal_count', 0)}")
    context_parts.append(f"Compliance score: {summary.get('compliance_score', 100)}%")

    if amount_col and "department" in df.columns:
        dept_totals = df.groupby("department")[amount_col].agg(["sum", "count", "mean"]).sort_values("sum", ascending=False)
        context_parts.append("\nDepartment breakdown:")
        for dept, row in dept_totals.head(5).iterrows():
            context_parts.append(f"  {dept}: ₹{row['sum']:,.2f} ({int(row['count'])} transactions, avg ₹{row['mean']:,.2f})")

    if amount_col and "vendor_canonical" in df.columns:
        vendor_totals = df.groupby("vendor_canonical")[amount_col].sum().sort_values(ascending=False)
        context_parts.append("\nTop 5 vendors:")
        for vendor, amt in vendor_totals.head(5).items():
            pct = (amt / summary.get("total_spend", 1)) * 100
            context_parts.append(f"  {vendor}: ₹{amt:,.2f} ({pct:.1f}%)")

    if "is_flagged" in df.columns and amount_col:
        flagged = df[df["is_flagged"] == True]
        if len(flagged) > 0:
            flagged_vendors = flagged.groupby("vendor_canonical" if "vendor_canonical" in flagged.columns else "vendor_raw")[amount_col].sum().sort_values(ascending=False)
            context_parts.append("\nVendors with most flagged transactions:")
            for vendor, amt in flagged_vendors.head(3).items():
                context_parts.append(f"  {vendor}: ₹{amt:,.2f} in flagged transactions")

    if "is_personal" in df.columns and amount_col:
        personal = df[df["is_personal"] == True]
        if len(personal) > 0:
            context_parts.append(f"\nPersonal expenses total: ₹{personal[amount_col].sum():,.2f} ({len(personal)} transactions)")

    if "receipt_attached" in df.columns:
        with_receipt = int(df["receipt_attached"].sum())
        total = len(df)
        rate = (with_receipt / total * 100) if total > 0 else 0
        context_parts.append(f"\nReceipt compliance: {rate:.1f}% ({with_receipt}/{total} with receipts)")

    if "entry_date" in df.columns and amount_col:
        date_df = df.copy()
        date_df["entry_date"] = pd.to_datetime(date_df["entry_date"], errors="coerce")
        date_df = date_df.dropna(subset=["entry_date"])
        if len(date_df) > 0:
            date_df["month"] = date_df["entry_date"].dt.to_period("M")
            monthly = date_df.groupby("month")[amount_col].sum()
            if len(monthly) > 1:
                context_parts.append(f"\nMonthly spend range: ₹{monthly.min():,.2f} to ₹{monthly.max():,.2f}")
                context_parts.append(f"Busiest month: {monthly.idxmax()} (₹{monthly.max():,.2f})")

    return "\n".join(context_parts)


def _chat_with_groq(message: str, data_context: str, system_prompt: str, max_tokens: int = 500) -> Optional[str]:
    client = _get_groq_client()
    if not client:
        return None

    try:
        response = client.chat.completions.create(
            model=_groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the expense data context:\n\n{data_context}\n\nUser question: {message}"},
            ],
            temperature=0.7,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq chat error: {e}")
        return None


def chat_with_ai(session_id: str, message: str, df: pd.DataFrame, summary: Optional[dict] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (response_text, provider_name) or (None, None) if no AI available.
    Provider can be "groq" or None.
    """
    if summary is None:
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

    data_context = _build_data_context(df, summary)

    system_prompt = (
        "You are an expert financial analyst AI assistant for ExpenseLens, "
        "an expense management and analysis platform. You have access to "
        "summarized expense data and can answer questions about spending patterns, "
        "anomalies, vendors, departments, compliance, and recommendations.\n\n"
        "Guidelines:\n"
        "- Be concise and data-driven in your responses\n"
        "- Use specific numbers from the data when answering\n"
        "- Format currency values as ₹X,XX,XXX.XX\n"
        "- If asked about something not in the data, say so clearly\n"
        "- Provide actionable insights when possible\n"
        "- Keep responses under 200 words unless the user asks for detail"
    )

    response = _chat_with_groq(message, data_context, system_prompt)
    if response:
        return response, "groq"

    return None, None


def generate_ai_insights(df: pd.DataFrame, summary: dict) -> Tuple[Optional[dict], Optional[str]]:
    """
    Returns (insights_dict, provider_name) or (None, None) if no AI available.
    Provider can be "groq" or None.
    """
    data_context = _build_data_context(df, summary)

    system_prompt = (
        "You are an expert financial analyst. Generate a comprehensive insights report "
        "from the provided expense data context. Return ONLY valid JSON matching this exact schema:\n"
        "{\n"
        '  "executive_summary": "string - 2-3 sentence overview",\n'
        '  "spending_patterns": ["string array - 3-5 key patterns"],\n'
        '  "vendor_analysis": [{"vendor": "name", "spend": number, "risk": "low/medium/high"}],\n'
        '  "department_trends": [{"department": "name", "total_spend": number, "percentage": number}],\n'
        '  "anomaly_insights": ["string array - 2-3 insights about anomalies"],\n'
        '  "recommendations": ["string array - 3-5 actionable recommendations"],\n'
        '  "risk_signals": ["string array - 2-4 risk signals identified"],\n'
        '  "employee_analysis": [{"submitted_by": "name", "total_spend": number, "transaction_count": number, "avg_spend": number, "compliance_rate": number}],\n'
        '  "vendor_risk": {"high_concentration_vendors": [{"vendor": "name", "spend_pct": number, "total_spend": number}], "vendors_with_anomalies": [{"vendor": "name", "anomaly_count": number}], "vendor_diversity_score": number},\n'
        '  "time_patterns": {"day_of_week_patterns": [{"day": "Monday", "total_spend": number, "count": number}], "busiest_month": "string", "quietest_month": "string", "month_end_spike": boolean},\n'
        '  "receipt_compliance": {"overall_rate": number, "by_department": [{"department": "name", "rate": number, "with_receipt": number, "total": number}], "high_value_missing_receipt": [{"txn_ref": "string", "amount": number, "vendor": "string", "department": "string"}]},\n'
        '  "duplicate_analysis": {"confirmed_duplicates": number, "duplicate_value": number, "potential_duplicates": number},\n'
        '  "high_value_transactions": {"top_1_percent": [{"txn_ref": "string", "amount": number, "vendor": "string", "department": "string", "submitted_by": "string", "is_flagged": boolean}], "threshold": number, "total_high_value": number, "count": number}\n'
        "}\n\n"
        "Do NOT include any text outside the JSON object. Do NOT use markdown code blocks."
    )

    def _parse_json_response(content: str) -> Optional[dict]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("AI response was not valid JSON")
            return None

    response = _chat_with_groq("Generate the insights report as JSON.", data_context, system_prompt, max_tokens=2000)
    if response:
        insights = _parse_json_response(response)
        if insights:
            return insights, "groq"

    return None, None
