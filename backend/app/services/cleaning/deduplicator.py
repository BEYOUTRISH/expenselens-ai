from typing import Any, Optional
from datetime import datetime, timedelta
from rapidfuzz import fuzz

from app.core.constants import ThresholdConfig


def _parse_date_for_compare(d: Any) -> Optional[datetime]:
    if isinstance(d, datetime):
        return d
    if isinstance(d, str):
        from .date_parser import parse_date

        result, _ = parse_date(d)
        if result:
            try:
                return datetime.strptime(result, "%Y-%m-%d")
            except ValueError:
                return None
    return None


def detect_duplicates(rows: list[dict]) -> list[dict]:
    enriched: list[dict] = []
    for row in rows:
        enriched.append(
            {
                **row,
                "is_duplicate": row.get("is_duplicate", False),
                "duplicate_of": row.get("duplicate_of", None),
                "under_review": row.get("under_review", False),
            }
        )

    groups: dict[tuple, list[int]] = {}
    for i, row in enumerate(enriched):
        vendor = str(row.get("vendor_canonical") or row.get("vendor", ""))
        amount_inr = row.get("amount_inr")
        submitted_by = str(row.get("submitted_by", ""))
        entry_date = _parse_date_for_compare(row.get("entry_date"))

        key = (vendor, amount_inr, submitted_by)
        if entry_date is None:
            continue

        found = False
        for (g_vendor, g_amount, g_submitted), indices in list(groups.items()):
            if key != (g_vendor, g_amount, g_submitted):
                continue
            for idx in indices:
                ref_date = _parse_date_for_compare(enriched[idx].get("entry_date"))
                if ref_date is not None:
                    diff = abs((entry_date - ref_date).days)
                    if diff <= ThresholdConfig.DUPLICATE_DAYS_WINDOW:
                        groups[(g_vendor, g_amount, g_submitted)].append(i)
                        found = True
                        break
            if found:
                break
        if not found:
            groups[key] = [i]

    for key, indices in groups.items():
        if len(indices) < 2:
            continue

        first_idx = indices[0]
        first_desc = str(enriched[first_idx].get("description", ""))

        for idx in indices[1:]:
            row = enriched[idx]
            desc = str(row.get("description", ""))
            desc_sim = fuzz.token_set_ratio(first_desc, desc) / 100.0
            amount_sim = True
            amt1 = enriched[first_idx].get("amount_inr")
            amt2 = row.get("amount_inr")
            if amt1 is not None and amt2 is not None:
                if abs(float(amt1) - float(amt2)) > 0.01:
                    amount_sim = False

            if desc_sim > ThresholdConfig.DUPLICATE_DESC_SIMILARITY and amount_sim:
                row["is_duplicate"] = True
                row["duplicate_of"] = str(
                    enriched[first_idx].get("txn_id", first_idx)
                )
                row["flag_reason"] = "CONFIRMED_DUPLICATE"
            else:
                enriched[first_idx]["under_review"] = True
                enriched[first_idx]["flag_reason"] = "UNDER_REVIEW"
                row["under_review"] = True
                row["flag_reason"] = "UNDER_REVIEW"

    return enriched
