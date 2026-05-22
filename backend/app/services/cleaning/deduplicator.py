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

    # Pre-parse dates once to avoid repeatedly parsing them in sorting/clustering loops
    parsed_dates = []
    for row in enriched:
        parsed_dates.append(_parse_date_for_compare(row.get("entry_date")))

    # O(N) Grouping by vendor, amount and submitter using a dictionary
    initial_groups: dict[tuple, list[int]] = {}
    for i, row in enumerate(enriched):
        entry_date = parsed_dates[i]
        if entry_date is None:
            continue
        vendor = str(row.get("vendor_canonical") or row.get("vendor", ""))
        amount_inr = row.get("amount_inr")
        submitted_by = str(row.get("submitted_by", ""))
        key = (vendor, amount_inr, submitted_by)

        if key not in initial_groups:
            initial_groups[key] = []
        initial_groups[key].append(i)

    # Partition each group into subgroups where items are close to each other in date
    final_groups: list[list[int]] = []
    for key, idxs in initial_groups.items():
        if len(idxs) < 2:
            continue

        # Sort indices in this group by date
        sorted_idxs = sorted(idxs, key=lambda x: parsed_dates[x])
        
        # Greedy clustering within the window
        current_subgroup = [sorted_idxs[0]]
        ref_date = parsed_dates[sorted_idxs[0]]

        for idx in sorted_idxs[1:]:
            curr_date = parsed_dates[idx]
            if abs((curr_date - ref_date).days) <= ThresholdConfig.DUPLICATE_DAYS_WINDOW:
                current_subgroup.append(idx)
            else:
                if len(current_subgroup) >= 2:
                    final_groups.append(current_subgroup)
                current_subgroup = [idx]
                ref_date = curr_date

        if len(current_subgroup) >= 2:
            final_groups.append(current_subgroup)

    # Perform description similarity comparison on each candidate subgroup
    for indices in final_groups:
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
                ref_txn_ref = enriched[first_idx].get("txn_ref") or enriched[first_idx].get("txn_id") or str(first_idx)
                row["duplicate_of"] = str(ref_txn_ref)
                row["flag_reason"] = "CONFIRMED_DUPLICATE"
            else:
                enriched[first_idx]["under_review"] = True
                enriched[first_idx]["flag_reason"] = "UNDER_REVIEW"
                row["under_review"] = True
                row["flag_reason"] = "UNDER_REVIEW"

    return enriched
