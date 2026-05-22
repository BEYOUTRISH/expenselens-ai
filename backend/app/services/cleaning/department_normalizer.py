from typing import Optional
from rapidfuzz import fuzz

from app.core.constants import CANONICAL_DEPARTMENTS, ThresholdConfig


def normalize_department(dept_raw: str) -> tuple[str, Optional[str]]:
    if not dept_raw or not dept_raw.strip():
        return "Unknown", "DEPARTMENT_UNRECOGNIZED"

    dept_stripped = dept_raw.strip()
    dept_lower = dept_stripped.lower()

    best_canonical: Optional[str] = None
    best_score = 0.0

    for canonical in CANONICAL_DEPARTMENTS:
        score = fuzz.ratio(dept_lower, canonical.lower()) / 100.0
        if score > best_score:
            best_score = score
            best_canonical = canonical

    if best_canonical is None or best_score < ThresholdConfig.DEPARTMENT_MATCH_THRESHOLD:
        return "Unknown", "DEPARTMENT_UNRECOGNIZED"

    if best_score < 1.0:
        return best_canonical, None

    return best_canonical, None
