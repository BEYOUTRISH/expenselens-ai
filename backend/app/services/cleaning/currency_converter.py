from typing import Any, Optional
import re

from .amount_parser import CURRENCY_CODES, CURRENCY_PREFIX_RE, CURRENCY_SUFFIX_RE
from app.core.constants import RuntimeSettings


def detect_currency(amount_str: str, currency_col_value: Any = None) -> str:
    if isinstance(amount_str, str):
        m = CURRENCY_PREFIX_RE.match(amount_str)
        if m:
            return m.group(1).upper()
        m = CURRENCY_SUFFIX_RE.match(amount_str)
        if m:
            return m.group(2).upper()

    if currency_col_value is not None:
        if isinstance(currency_col_value, str):
            val = currency_col_value.strip().upper()
            if val in CURRENCY_CODES:
                return val

    return "INR"


def convert_to_inr(amount: float, from_currency: str) -> tuple[float, float]:
    from_currency = from_currency.upper().strip()
    rate = RuntimeSettings.get_exchange_rate(from_currency)
    amount_inr = round(amount * rate, 2)
    return amount_inr, rate
