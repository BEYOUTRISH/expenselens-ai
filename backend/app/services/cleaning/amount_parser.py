from typing import Any, Optional, Pattern
import re


SENTINEL_VALUES: set[str] = {"tbd", "n/a", "--", "nil", "none", "", "null"}

CURRENCY_SYMBOLS: dict[str, str] = {
    "\u20b9": "INR",
    "$": "USD",
    "\u20ac": "EUR",
    "\u00a3": "GBP",
    "\u20a8": "INR",
    "\u20aa": "INR",
}

CURRENCY_CODES: list[str] = [
    "INR",
    "USD",
    "EUR",
    "GBP",
    "SGD",
    "AED",
    "JPY",
    "CNY",
    "CHF",
    "AUD",
    "CAD",
    "HKD",
    "MYR",
    "THB",
]

CURRENCY_PREFIX_RE: Pattern = re.compile(
    r"^\s*("
    + "|".join(re.escape(c) for c in CURRENCY_CODES)
    + r")\s+"
    + r"([\d\s,.-]+)\s*$",
    re.IGNORECASE,
)

CURRENCY_SUFFIX_RE: Pattern = re.compile(
    r"^\s*([\d\s,.-]+)\s+("
    + "|".join(re.escape(c) for c in CURRENCY_CODES)
    + r")\s*$",
    re.IGNORECASE,
)

INDIAN_COMMA_PATTERN: Pattern = re.compile(
    r"^-?\s*[\u20b9$€£\u20a8\u20aa]?\s*"
    r"\d{1,2},(?:\d{2},)*\d{3}"
    r"(?:\.\d+)?\s*$"
)

STANDARD_COMMA_PATTERN: Pattern = re.compile(
    r"^-?\s*[\u20b9$€£\u20a8\u20aa]?\s*"
    r"\d{1,3}(?:,\d{3})+(?:\.\d+)?\s*$"
)

NUMBER_WITH_COMMAS: Pattern = re.compile(
    r"^-?\s*[\u20b9$€£\u20a8\u20aa]?\s*" r"[\d,]+(?:\.\d+)?" r"\s*$"
)

SYMBOL_PREFIX_RE: Pattern = re.compile(
    r"^\s*([\u20b9$€£\u20a8\u20aa])\s*([\d,.-]+)\s*$"
)


def normalize_number_str(raw: str) -> str:
    s = raw.strip()
    for sym in CURRENCY_SYMBOLS:
        s = s.replace(sym, "")
    return s.strip()


def is_indian_notation(s: str) -> bool:
    cleaned = normalize_number_str(s)
    if not re.match(r"^-?[\d,]+(?:\.\d+)?$", cleaned):
        return False
    if cleaned.startswith("-"):
        cleaned = cleaned[1:]
    parts = cleaned.split(".")
    int_part = parts[0]
    if "," not in int_part:
        return False
    segments = int_part.split(",")
    if len(segments) < 2:
        return False

    last_seg = segments[-1]
    if len(last_seg) != 3:
        return False

    for i in range(len(segments) - 1):
        seg = segments[i]
        if i == 0:
            if len(seg) < 1 or len(seg) > 2:
                return False
        else:
            if len(seg) != 2:
                return False

    return True


def parse_comma_number(s: str) -> float:
    s = normalize_number_str(s)
    negative = False
    if s.startswith("-"):
        negative = True
        s = s[1:]
    s = s.replace(",", "")
    val = float(s)
    if negative:
        val = -val
    return val


def extract_embedded_currency(s: str) -> Optional[tuple[float, str]]:
    m = CURRENCY_PREFIX_RE.match(s)
    if m:
        code = m.group(1).upper()
        num_part = m.group(2).strip()
        return (parse_comma_number(num_part), code)

    m = CURRENCY_SUFFIX_RE.match(s)
    if m:
        code = m.group(2).upper()
        num_part = m.group(1).strip()
        return (parse_comma_number(num_part), code)

    return None


def extract_symbol_currency(s: str) -> Optional[tuple[float, str]]:
    m = SYMBOL_PREFIX_RE.match(s)
    if m:
        sym = m.group(1)
        code = CURRENCY_SYMBOLS.get(sym, "INR")
        num_str = m.group(2).strip()
        return (parse_comma_number(num_str), code)
    return None


def parse_amount(
    value: Any,
) -> tuple[Optional[float], Optional[str], Optional[str]]:
    if value is None:
        return None, None, "SENTINEL: value is None"

    if isinstance(value, (int, float)):
        return float(value), None, None

    if isinstance(value, str):
        s = value.strip()
        if s.lower() in SENTINEL_VALUES:
            return None, None, "SENTINEL"

        embedded = extract_embedded_currency(s)
        if embedded:
            return embedded[0], embedded[1], None

        symbolic = extract_symbol_currency(s)
        if symbolic:
            return symbolic[0], symbolic[1], None

        cleaned = normalize_number_str(s)
        if cleaned.startswith("-"):
            cleaned = cleaned[1:]
        cleaned = cleaned.strip()

        if re.match(r"^-?[\d,]+(?:\.\d+)?$", cleaned):
            return parse_comma_number(s), None, None

        return None, None, f"UNPARSEABLE_AMOUNT: unrecognized format '{s}'"

    return None, None, f"UNPARSEABLE_AMOUNT: unsupported type {type(value).__name__}"
