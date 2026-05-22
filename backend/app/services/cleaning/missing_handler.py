from typing import Any

from app.core.constants import SENTINEL_VALUES, STANDARD_COLUMNS

REQUIRED_FIELDS: list[str] = [
    "txn_ref",
    "entry_date",
    "amount_raw",
    "amount_inr",
    "vendor",
]


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        if value.strip().lower() in SENTINEL_VALUES:
            return True
        return False
    return False


def _is_sentinel(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in SENTINEL_VALUES
    return False


def classify_missing(field: str, value: Any) -> tuple[str, str]:
    field_lower = field.strip().lower()

    if not _is_missing(value):
        pass

    if field_lower == "txn_ref" and _is_missing(value):
        return "CRITICAL", f"Required field '{field}' is missing"
    if field_lower == "amount_raw" and (_is_missing(value) or _is_sentinel(value)):
        return "CRITICAL", f"Required field '{field}' is missing or sentinel"
    if field_lower == "vendor" and _is_missing(value):
        return "WARNING", f"Required field '{field}' is missing, cannot infer vendor"
    if field_lower == "cost_center" and _is_missing(value):
        return "WARNING", f"Field '{field}' is missing"
    if field_lower == "submitted_by" and _is_missing(value):
        return "WARNING", f"Field '{field}' is missing"
    if field_lower == "description" and _is_missing(value):
        return "INFO", f"Field '{field}' is missing"
    if field_lower == "department" and _is_missing(value):
        return "INFO", "Field 'department' is missing but cost_center may be present"

    if _is_missing(value):
        return "INFO", f"Field '{field}' is missing"

    return "INFO", f"Field '{field}' is present"
