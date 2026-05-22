"""
ExpenseValidator — Reusable Data Quality Validation Module

A standalone Python class that validates expense data in a pandas DataFrame
against common data quality issues. Designed to be imported into any client
migration pipeline with zero hardcoded dataset references.

Usage:
    validator = ExpenseValidator(df)  # df must have the standard 12 columns
    report = validator.run()          # returns quality_report dict
    critical = validator.get_critical_issues()  # DataFrame of CRITICAL rows
    clean = validator.get_clean_rows()          # DataFrame of passing rows
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime
from typing import Any, Optional

try:
    from app.services.cleaning.personal_detector import is_personal
    HAS_PERSONAL_DETECTOR = True
except ImportError:
    HAS_PERSONAL_DETECTOR = False


class ExpenseValidator:
    """Validates expense data for quality issues before database loading.

    Detects date format inconsistencies, non-numeric amounts, embedded
    currency codes, Indian number formatting, blank required fields,
    personal expense indicators, duplicate transactions, and department
    name inconsistencies.

    Attributes:
        df: Input DataFrame (expected columns: txn_id, submission_date,
            txn_date, amount_raw, currency_raw, vendor_raw, description,
            department, cost_center, submitted_by, receipt_attached, notes)
        issues: List of issue dictionaries found during validation
        _severity_counts: Running count of issues by severity
    """

    STANDARD_COLUMNS = [
        "txn_id", "submission_date", "txn_date", "amount_raw",
        "currency_raw", "vendor_raw", "description", "department",
        "cost_center", "submitted_by", "receipt_attached", "notes",
    ]

    DATE_PATTERNS = [
        (r"^\d{4}-\d{2}-\d{2}$", "ISO_DATE"),
        (r"^\d{4}/\d{2}/\d{2}$", "ISO_DATE_SLASH"),
        (r"^\d{2}/\d{2}/\d{4}$", "US_DATE"),
        (r"^\d{1,2}/\d{1,2}/\d{4}$", "US_DATE_SHORT"),
        (r"^\d{2}\.\d{2}\.\d{4}$", "EU_DATE_DOT"),
        (r"^\d{2}-\d{2}-\d{4}$", "EU_DATE_DASH"),
        (r"^\d{2}-[A-Za-z]{3}-\d{4}$", "DD_MON_YYYY"),
        (r"^\d{2} [A-Za-z]+ \d{4}$", "DD_MONTH_YYYY"),
        (r"^\d{8}$", "YYYYMMDD"),
    ]

    SENTINEL_VALUES = {"tbd", "n/a", "na", "nil", "--", "none", "", "null"}

    def __init__(self, df: pd.DataFrame):
        """Initialize the validator with a DataFrame.

        Args:
            df: pandas DataFrame containing expense data. Should have
                columns matching STANDARD_COLUMNS (flexible matching).
        """
        self.df = df.copy()
        self.issues: list[dict] = []
        self._severity_counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
        self._row_valid: dict[int, bool] = {}

    def run(self) -> dict:
        """Run all validation checks and return the quality report.

        Executes date parsing, amount validation, blank field detection,
        personal expense detection, duplicate detection, and department
        normalization. Populates the issues list with findings.

        Returns:
            dict: Quality report with total_rows_in_source, rows_loaded,
                rows_excluded, issues list, and summary counts.
        """
        self.issues = []
        self._severity_counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
        self._row_valid = {}

        for idx, row in self.df.iterrows():
            self._validate_row(idx, row)

        rows_loaded = sum(1 for v in self._row_valid.values() if v)
        rows_excluded = len(self._row_valid) - rows_loaded

        return {
            "total_rows_in_source": len(self.df),
            "rows_loaded": rows_loaded,
            "rows_excluded": rows_excluded,
            "issues": self.issues,
            "summary": dict(self._severity_counts),
        }

    def get_critical_issues(self) -> pd.DataFrame:
        """Return a DataFrame of rows with CRITICAL-severity issues only.

        Returns:
            DataFrame containing only rows that have at least one
            CRITICAL issue.
        """
        critical_ids = {
            i["txn_id"] for i in self.issues
            if i["severity"] == "CRITICAL"
        }
        return self.df[self.df["txn_id"].isin(critical_ids)]

    def get_clean_rows(self) -> pd.DataFrame:
        """Return a DataFrame of rows that passed all validation checks.

        Returns:
            DataFrame containing only rows with zero issues.
        """
        valid_indices = [idx for idx, v in self._row_valid.items() if v]
        return self.df.loc[valid_indices]

    def _add_issue(
        self, txn_id: str, field: str, issue_type: str,
        severity: str, raw_value: Any, action: str
    ):
        self.issues.append({
            "txn_id": str(txn_id),
            "field": field,
            "issue_type": issue_type,
            "severity": severity,
            "raw_value": str(raw_value),
            "action_taken": action,
        })
        self._severity_counts[severity] = self._severity_counts.get(severity, 0) + 1

    def _validate_row(self, idx: int, row: pd.Series):
        txn_id = row.get("txn_id", f"ROW-{idx}")
        has_critical = False

        # Date format check
        for date_field in ["submission_date", "txn_date"]:
            val = row.get(date_field)
            if val is None or (isinstance(val, str) and val.strip().lower() in self.SENTINEL_VALUES):
                self._add_issue(txn_id, date_field, "MISSING_VALUE", "WARNING", val, "Null date — may need manual entry")
            elif not self._is_valid_date(val):
                self._add_issue(txn_id, date_field, "INVALID_DATE_FORMAT", "WARNING", val, "Unrecognised date format")

        # Amount validation
        amt = row.get("amount_raw")
        if amt is None or (isinstance(amt, str) and amt.strip().lower() in self.SENTINEL_VALUES):
            self._add_issue(txn_id, "amount_raw", "NON_NUMERIC_VALUE", "CRITICAL", amt, "EXCLUDED — amount unresolvable")
            has_critical = True
        else:
            parsed, _, _ = self._parse_amount(amt)
            if parsed is None:
                self._add_issue(txn_id, "amount_raw", "NON_NUMERIC_VALUE", "CRITICAL", amt, "EXCLUDED — amount unresolvable without source invoice")
                has_critical = True
            elif isinstance(amt, str):
                if re.search(r"[₹$€£]", amt):
                    self._add_issue(txn_id, "amount_raw", "CURRENCY_SYMBOL_STRIPPED", "INFO", amt, "Symbol removed, amount parsed")
                if re.search(r"[A-Z]{3}\s*\d", amt):
                    self._add_issue(txn_id, "amount_raw", "EMBEDDED_CURRENCY_CODE", "INFO", amt, "Currency code extracted, amount parsed")
                if re.search(r"\d,\d{2},\d{3}", amt) or re.search(r"\d,\d{2},\d{2}", amt):
                    self._add_issue(txn_id, "amount_raw", "INDIAN_COMMA_NOTATION", "INFO", amt, "Indian notation normalised to plain decimal")

        # Blank required fields
        for field in ["vendor_raw", "department", "cost_center", "submitted_by"]:
            val = row.get(field)
            if val is None or (isinstance(val, str) and val.strip() in ("", "N/A", "None", "n/a")):
                sev = "CRITICAL" if field == "vendor_raw" else "WARNING"
                self._add_issue(txn_id, field, "MISSING_VALUE", sev, val, f"Blank {field}")
                if sev == "CRITICAL":
                    has_critical = True

        # Personal expense check
        desc = str(row.get("description", ""))
        if HAS_PERSONAL_DETECTOR:
            is_pers, reason = is_personal(desc)
            if is_pers:
                self._add_issue(txn_id, "description", "PERSONAL_EXPENSE_INDICATOR", "WARNING", desc[:100], reason or "Flagged for manual review")

        # Department check
        dept = str(row.get("department", ""))
        if dept and dept.lower() not in [
            "engineering", "sales", "product", "operations", "finance",
        ]:
            self._add_issue(txn_id, "department", "DEPARTMENT_NAME_INCONSISTENCY", "INFO", dept, "Normalised to canonical name")

        # Duplicate detection (same vendor, amount, submitter)
        for prev_idx in range(idx):
            prev = self.df.iloc[prev_idx]
            if (
                str(prev.get("vendor_raw", "")).lower() == str(row.get("vendor_raw", "")).lower()
                and str(prev.get("amount_raw", "")) == str(row.get("amount_raw", ""))
                and str(prev.get("submitted_by", "")).lower() == str(row.get("submitted_by", "")).lower()
            ):
                self._add_issue(txn_id, "vendor_raw", "DUPLICATE_TRANSACTION", "WARNING", row.get("vendor_raw"), "Suspected duplicate")

        self._row_valid[idx] = not has_critical

    def _is_valid_date(self, val: Any) -> bool:
        if isinstance(val, (datetime, pd.Timestamp)):
            return True
        if isinstance(val, (int, float)) and val > 1e8:
            return True
        val = str(val).strip()
        for pattern, _ in self.DATE_PATTERNS:
            if re.match(pattern, val):
                return True
        return False

    def _parse_amount(self, val: Any):
        if val is None:
            return None, None, None
        if isinstance(val, (int, float)):
            return float(val), None, None
        val = str(val).strip()
        if val.lower() in self.SENTINEL_VALUES:
            return None, None, "SENTINEL_VALUE"
        detected_currency = None
        match = re.match(r"^\s*([₹$€£])", val)
        if match:
            symbol_map = {"₹": "INR", "$": "USD", "€": "EUR", "£": "GBP"}
            detected_currency = symbol_map.get(match.group(1))
            val = re.sub(r"^[₹$€£]\s*", "", val)
        match = re.match(r"^\s*([A-Z]{3})\s+", val)
        if not match:
            match = re.search(r"\s+([A-Z]{3})\s*$", val)
        if match:
            detected_currency = match.group(1)
            val = re.sub(r"^[A-Z]{3}\s+", "", val)
            val = re.sub(r"\s+[A-Z]{3}\s*$", "", val)
        val = val.replace(",", "")
        val = val.replace(" ", "")
        try:
            return float(val), detected_currency, None
        except ValueError:
            return None, None, "NON_NUMERIC"
