from typing import Any, Optional
from datetime import datetime, timezone
import re
from dateutil import parser as dateutil_parser


ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_SLASH_RE = re.compile(r"^\d{4}/\d{2}/\d{2}$")
US_DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")
EU_DATE_RE = re.compile(r"^\d{1,2}\.\d{1,2}\.\d{4}$")
EU_DASH_RE = re.compile(r"^\d{1,2}-\d{1,2}-\d{4}$")
DD_MON_YYYY_RE = re.compile(
    r"^\d{1,2}[- ](Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[- ]\d{4}$",
    re.IGNORECASE,
)
YYYYMMDD_RE = re.compile(r"^\d{8}$")
EPOCH_RE = re.compile(r"^\d+(\.\d+)?$")


def parse_date(value: Any) -> tuple[Optional[str], Optional[str]]:
    if value is None:
        return None, "UNPARSEABLE_DATE: value is None"

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d"), None

    if isinstance(value, str):
        value_stripped = value.strip()
        if not value_stripped:
            return None, "UNPARSEABLE_DATE: empty string"

        if ISO_DATE_RE.match(value_stripped):
            try:
                datetime.strptime(value_stripped, "%Y-%m-%d")
                return value_stripped, None
            except ValueError:
                pass

        if ISO_SLASH_RE.match(value_stripped):
            try:
                dt = datetime.strptime(value_stripped, "%Y/%m/%d")
                return dt.strftime("%Y-%m-%d"), None
            except ValueError:
                pass

        if US_DATE_RE.match(value_stripped):
            for fmt in ("%m/%d/%Y", "%m/%d/%y"):
                try:
                    dt = datetime.strptime(value_stripped, fmt)
                    return dt.strftime("%Y-%m-%d"), None
                except ValueError:
                    continue

        if EU_DATE_RE.match(value_stripped):
            try:
                dt = datetime.strptime(value_stripped, "%d.%m.%Y")
                return dt.strftime("%Y-%m-%d"), None
            except ValueError:
                pass

        if EU_DASH_RE.match(value_stripped):
            try:
                dt = datetime.strptime(value_stripped, "%d-%m-%Y")
                return dt.strftime("%Y-%m-%d"), None
            except ValueError:
                pass

        if DD_MON_YYYY_RE.match(value_stripped):
            try:
                dt = datetime.strptime(value_stripped.replace("-", " "), "%d %b %Y")
                return dt.strftime("%Y-%m-%d"), None
            except ValueError:
                try:
                    dt = datetime.strptime(
                        value_stripped.replace("-", " "), "%d %B %Y"
                    )
                    return dt.strftime("%Y-%m-%d"), None
                except ValueError:
                    pass

        if YYYYMMDD_RE.match(value_stripped):
            try:
                dt = datetime.strptime(value_stripped, "%Y%m%d")
                return dt.strftime("%Y-%m-%d"), None
            except ValueError:
                pass

        try:
            dt = dateutil_parser.parse(value_stripped, dayfirst=False)
            return dt.strftime("%Y-%m-%d"), None
        except (ValueError, OverflowError):
            pass

        return None, f"UNPARSEABLE_DATE: unrecognized format '{value_stripped}'"

    if isinstance(value, (int, float)):
        if value > 1e8:
            try:
                dt = datetime.fromtimestamp(value, tz=timezone.utc)
                return dt.strftime("%Y-%m-%d"), None
            except (OSError, OverflowError, ValueError):
                return None, f"UNPARSEABLE_DATE: invalid epoch timestamp {value}"
        return None, f"UNPARSEABLE_DATE: numeric value {value} below epoch threshold"

    return None, f"UNPARSEABLE_DATE: unsupported type {type(value).__name__}"
