from typing import Any, Optional
from rapidfuzz import fuzz, process

from app.core.constants import ThresholdConfig, CANONICAL_SCHEMA_FIELDS


KNOWN_PATTERNS: dict[str, list[str]] = {
    "txn_id": ["txn_id", "transaction_id", "ref", "ref_no"],
    "submission_date": ["submission_date", "submit_date", "date_submitted"],
    "txn_date": ["txn_date", "transaction_date", "date", "expense_date"],
    "amount_raw": ["amount_raw", "amount", "total", "spend", "amt"],
    "currency_raw": ["currency_raw", "currency", "cur", "ccy"],
    "vendor_raw": ["vendor_raw", "vendor", "merchant", "supplier", "payee"],
    "description": ["description", "desc", "narrative", "note", "purpose"],
    "department": ["department", "dept", "division", "unit"],
    "cost_center": ["cost_center", "cost_centre", "cc", "cost_code"],
    "submitted_by": ["submitted_by", "submitter", "employee", "emp", "name"],
    "receipt_attached": ["receipt_attached", "receipt", "has_receipt", "receipt_yn"],
    "notes": ["notes", "comment", "remarks", "memo"],
}


def detect_schema(
    headers: list[str],
) -> tuple[dict[str, int], dict[str, float]]:
    mapping: dict[str, int] = {}
    confidence: dict[str, float] = {}
    seen_indices: set[int] = set()

    flattened: list[tuple[str, str]] = []
    for canonical, aliases in KNOWN_PATTERNS.items():
        for alias in aliases:
            flattened.append((canonical, alias))

    for idx, header in enumerate(headers):
        header_stripped = header.strip()
        if not header_stripped:
            canonical_name = f"unknown_{idx}"
            mapping[canonical_name] = idx
            confidence[canonical_name] = 0.0
            continue

        best_match: Optional[tuple[str, str]] = None
        best_score = 0.0
        for canonical, alias in flattened:
            score = fuzz.token_set_ratio(header_stripped.lower(), alias.lower()) / 100.0
            if score > best_score:
                best_score = score
                best_match = (canonical, alias)

        if best_match is not None and best_score >= ThresholdConfig.SCHEMA_MATCH_THRESHOLD:
            canonical_name = best_match[0]
            if canonical_name in mapping:
                existing_idx = mapping[canonical_name]
                if best_score > confidence[canonical_name]:
                    seen_indices.discard(existing_idx)
                    mapping[canonical_name] = idx
                    confidence[canonical_name] = best_score
                    seen_indices.add(idx)
            else:
                mapping[canonical_name] = idx
                confidence[canonical_name] = best_score
                seen_indices.add(idx)
        else:
            canonical_name = f"unknown_{idx}"
            mapping[canonical_name] = idx
            confidence[canonical_name] = 0.0

    return mapping, confidence
