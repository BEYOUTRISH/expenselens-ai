"""
ExpenseLens AI - Generic Data Cleaning Engine
Orchestrates the full cleaning pipeline for any uploaded expense file.
"""

import logging
import re
from typing import Any, Optional
from datetime import datetime, date
import pandas as pd
import numpy as np

from app.services.cleaning.schema_detector import detect_schema
from app.services.cleaning.date_parser import parse_date
from app.services.cleaning.amount_parser import parse_amount
from app.services.cleaning.currency_converter import detect_currency, convert_to_inr
from app.services.cleaning.vendor_resolver import resolve_vendor
from app.services.cleaning.department_normalizer import normalize_department
from app.services.cleaning.deduplicator import detect_duplicates
from app.services.cleaning.personal_detector import is_personal
from app.services.cleaning.missing_handler import classify_missing
from app.services.cleaning.quality_reporter import generate_report
from app.core.constants import RuntimeSettings, ThresholdConfig

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def _is_valid_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

def _parse_date_safe(date_str: Any) -> Optional[date]:
    if isinstance(date_str, datetime):
        return date_str.date()
    if isinstance(date_str, date):
        return date_str
    if not isinstance(date_str, str):
        return None
    try:
        parsed, _ = parse_date(date_str)
        if parsed:
            return datetime.strptime(parsed, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        pass
    return None


class ExpenseCleaner:
    def __init__(self, base_currency: str = "INR"):
        self.base_currency = base_currency
        self.issues: list[dict] = []
        self.schema_map: dict = {}

    def _add_issue(
        self, txn_id: str, field: str, issue_type: str,
        severity: str, raw_value: Any, action: str
    ):
        self.issues.append({
            "txn_id": txn_id,
            "field": field,
            "issue_type": issue_type,
            "severity": severity,
            "raw_value": str(raw_value) if raw_value is not None else "NULL",
            "action_taken": action,
        })

    def _normalize_receipt(self, val: Any) -> bool:
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return bool(val)
        if isinstance(val, str):
            return val.strip().lower() in ("yes", "true", "1", "y")
        return False

    def _normalize_txn_id(self, val: Any) -> Optional[str]:
        if val is None:
            return None
        s = str(val).strip()
        return s if s else None

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        self.issues = []
        schema_mapping, _ = detect_schema(list(df.columns))
        self.schema_map = schema_mapping

        logger.info(f"Schema map: {self.schema_map}")

        results = []
        excluded_count = 0

        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            cleaned = self._clean_row(row_dict, idx)
            if cleaned.get("_excluded"):
                excluded_count += 1
            else:
                results.append(cleaned)

        cleaned_df = pd.DataFrame(results)

        deduped_list = detect_duplicates(results)
        cleaned_df = pd.DataFrame(deduped_list)

        report = generate_report(
            original_rows=len(df),
            cleaned_rows=results,
            issues=self.issues,
        )

        self.quality_report = report
        logger.info(f"Cleaning complete: {report['rows_loaded']} loaded, {report['rows_excluded']} excluded")

        return cleaned_df

    def _get_col(self, row: dict, canonical: str) -> Any:
        if canonical in self.schema_map:
            col_idx = self.schema_map[canonical]
            cols = list(row.keys())
            if col_idx < len(cols):
                return row[cols[col_idx]]
        return None

    def _clean_row(self, row: dict, idx: int) -> dict:
        result = {"_row_index": idx, "_excluded": False}

        txn_id = self._normalize_txn_id(self._get_col(row, "txn_id"))
        if txn_id:
            result["txn_ref"] = txn_id
        else:
            result["txn_ref"] = f"ROW-{idx+1:06d}"
            self._add_issue(result["txn_ref"], "txn_id", "MISSING_VALUE", "WARNING", None, "Auto-generated txn_ref")

        submission_raw = self._get_col(row, "submission_date")
        sub_date, sub_issue = parse_date(submission_raw)
        result["submission_date"] = sub_date
        if sub_issue:
            self._add_issue(result["txn_ref"], "submission_date", "INVALID_DATE", "WARNING", submission_raw, sub_issue)

        txn_raw = self._get_col(row, "txn_date")
        txn_date, txn_issue = parse_date(txn_raw)
        result["entry_date"] = txn_date
        if txn_issue:
            self._add_issue(result["txn_ref"], "txn_date", "INVALID_DATE", "WARNING", txn_raw, txn_issue)
        
        if txn_date:
            parsed_txn_date = _parse_date_safe(txn_date)
            today = date.today()
            if parsed_txn_date:
                if parsed_txn_date > today:
                    self._add_issue(
                        result["txn_ref"], "txn_date", "FUTURE_DATE",
                        "WARNING", txn_date, "Transaction date is in the future"
                    )
                    result["is_flagged"] = True
                    result["flag_reason"] = "FUTURE_DATE"
                if parsed_txn_date.year < today.year - 10:
                    self._add_issue(
                        result["txn_ref"], "txn_date", "DATE_TOO_OLD",
                        "INFO", txn_date, "Transaction date is more than 10 years old"
                    )
                if parsed_txn_date.weekday() >= 5:
                    self._add_issue(
                        result["txn_ref"], "txn_date", "WEEKEND_TRANSACTION",
                        "INFO", txn_date, "Transaction submitted on weekend"
                    )

        amount_raw = self._get_col(row, "amount_raw")
        currency_col = self._get_col(row, "currency_raw")
        parsed_amount, detected_currency, amount_issue = parse_amount(amount_raw)

        currency = detected_currency or detect_currency(str(amount_raw) if amount_raw else "", currency_col)

        result["original_currency"] = currency

        if parsed_amount is not None:
            result["amount_raw_value"] = float(parsed_amount)
            
            if float(parsed_amount) < 0:
                self._add_issue(
                    result["txn_ref"], "amount_raw", "NEGATIVE_AMOUNT",
                    "WARNING", amount_raw, "Negative amount - may be refund or data entry error"
                )
                result["is_flagged"] = True
                result["flag_reason"] = "NEGATIVE_AMOUNT"
            
            receipt_threshold = RuntimeSettings.get_receipt_threshold()
            if float(parsed_amount) > receipt_threshold:
                result["high_value_transaction"] = True
            
            try:
                amount_inr, rate = convert_to_inr(parsed_amount, currency)
                result["amount_inr"] = round(float(amount_inr), 2)
                result["exchange_rate_used"] = float(rate) if rate != 1.0 else None
            except Exception as e:
                self._add_issue(result["txn_ref"], "amount_raw", "CONVERSION_ERROR", "CRITICAL", amount_raw, str(e))
                result["_excluded"] = True
                return result
        else:
            result["amount_raw_value"] = None
            result["amount_inr"] = None
            severity = "CRITICAL"
            if amount_issue and "sentinel" in amount_issue.lower():
                severity = "CRITICAL"
            elif amount_issue and "empty" in amount_issue.lower():
                severity = "CRITICAL"
            self._add_issue(result["txn_ref"], "amount_raw", "NON_NUMERIC_VALUE", severity, amount_raw, amount_issue or "EXCLUDED")
            result["_excluded"] = True
            return result

        vendor_raw = str(self._get_col(row, "vendor_raw") or "")
        description = str(self._get_col(row, "description") or "")
        vendor_canonical, vendor_alias, vendor_issue = resolve_vendor(vendor_raw, description)
        result["vendor_raw"] = vendor_raw
        result["vendor_canonical"] = vendor_canonical
        if vendor_issue:
            sev = "WARNING" if "UNKNOWN" in vendor_issue else "INFO"
            self._add_issue(result["txn_ref"], "vendor_raw", vendor_issue, sev, vendor_raw, f"Resolved to: {vendor_canonical}")

        dept_raw = str(self._get_col(row, "department") or "")
        dept_canonical, dept_issue = normalize_department(dept_raw)
        result["department"] = dept_canonical
        if dept_issue:
            self._add_issue(result["txn_ref"], "department", dept_issue, "INFO", dept_raw, f"Corrected to: {dept_canonical}")

        cost_center = str(self._get_col(row, "cost_center") or "")
        if cost_center in ("", "N/A", "None", "nan"):
            cost_center = None
            self._add_issue(result["txn_ref"], "cost_center", "MISSING_VALUE", "WARNING", cost_center, "Cost center missing")
        result["cost_center"] = cost_center

        submitted_by = self._get_col(row, "submitted_by")
        if submitted_by is None or (isinstance(submitted_by, str) and submitted_by.strip() in ("", "N/A", "None")):
            submitted_by = None
            self._add_issue(result["txn_ref"], "submitted_by", "MISSING_VALUE", "WARNING", submitted_by, "Submitted by missing")
        else:
            submitted_str = str(submitted_by) if submitted_by else ""
            if "@" in submitted_str and not _is_valid_email(submitted_str):
                self._add_issue(
                    result["txn_ref"], "submitted_by", "INVALID_EMAIL_FORMAT",
                    "WARNING", submitted_str, "Email format appears invalid"
                )
        result["submitted_by"] = str(submitted_by) if submitted_by else ""

        receipt_raw = self._get_col(row, "receipt_attached")
        result["receipt_attached"] = self._normalize_receipt(receipt_raw)

        if description:
            result["description"] = str(description).strip()
        else:
            result["description"] = ""
            self._add_issue(result["txn_ref"], "description", "MISSING_VALUE", "INFO", description, "Empty description")

        is_pers, pers_reason = is_personal(description)
        result["is_personal"] = is_pers
        
        existing_flag = result.get("is_flagged", False)
        existing_reason = result.get("flag_reason", None)
        
        if is_pers:
            result["is_flagged"] = True
            if existing_reason:
                result["flag_reason"] = f"{existing_reason}; {pers_reason}"
            else:
                result["flag_reason"] = pers_reason
            self._add_issue(result["txn_ref"], "description", "PERSONAL_EXPENSE", "WARNING", description[:100], pers_reason)
        else:
            result["is_flagged"] = existing_flag
            result["flag_reason"] = existing_reason

        notes = self._get_col(row, "notes")
        result["notes"] = str(notes).strip() if notes else ""

        result["approval_status"] = "pending"
        result["is_duplicate"] = False
        result["duplicate_of"] = None

        return result

    def get_report(self) -> dict:
        return getattr(self, "quality_report", {
            "total_rows_in_source": 0,
            "rows_loaded": 0,
            "rows_excluded": 0,
            "issues": [],
            "summary": {"CRITICAL": 0, "WARNING": 0, "INFO": 0},
        })
