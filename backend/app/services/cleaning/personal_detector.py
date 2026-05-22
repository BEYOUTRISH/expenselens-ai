"""
Personal Expense Detection Module

Uses regex with word boundaries and negation handling for accurate classification.
"""

from typing import Optional, List, Tuple
import re

from app.core.constants import (
    PERSONAL_KEYWORDS,
    PERSONAL_KEYWORD_WEIGHTS,
    create_word_boundary_pattern,
    has_negation_prefix,
    is_business_context,
)


PERSONAL_PATTERNS_CACHE: dict[str, re.Pattern] = {}
PERSONAL_SCORE_THRESHOLD: float = 0.7


def _get_pattern(keyword: str) -> re.Pattern:
    """Get or compile a regex pattern for a keyword."""
    global PERSONAL_PATTERNS_CACHE
    if keyword not in PERSONAL_PATTERNS_CACHE:
        PERSONAL_PATTERNS_CACHE[keyword] = create_word_boundary_pattern(keyword)
    return PERSONAL_PATTERNS_CACHE[keyword]


def is_personal(description: str) -> Tuple[bool, Optional[str]]:
    """
    Detect if a description indicates a personal expense using:
    1. Word boundary regex matching (avoids false positives like 'son' in 'person')
    2. Negation handling (ignores 'not personal', 'for business', etc.)
    3. Weighted scoring instead of first-match
    
    Returns: (is_personal_flag, reason_string)
    """
    if not description or not description.strip():
        return False, None
    
    desc_lower = description.lower()
    matched_keywords: List[Tuple[str, float, int]] = []
    
    for keyword in PERSONAL_KEYWORDS:
        pattern = _get_pattern(keyword)
        matches = list(pattern.finditer(description))
        
        for match in matches:
            match_start = match.start()
            
            if has_negation_prefix(description, match_start, keyword):
                continue
            
            if is_business_context(description, keyword):
                continue
            
            weight = PERSONAL_KEYWORD_WEIGHTS.get(keyword, 0.7)
            matched_keywords.append((keyword, weight, match_start))
    
    if not matched_keywords:
        return False, None
    
    matched_keywords.sort(key=lambda x: (-x[1], x[2]))
    
    total_score = sum(weight for _, weight, _ in matched_keywords)
    top_keyword = matched_keywords[0][0]
    
    if len(matched_keywords) > 1:
        other_keywords = ", ".join([f"'{kw}'" for kw, _, _ in matched_keywords[1:3]])
        reason = (
            f"PERSONAL_EXPENSE: description contains '{top_keyword}' "
            f"(score: {total_score:.1f}, also found: {other_keywords})"
        )
    else:
        reason = f"PERSONAL_EXPENSE: description contains '{top_keyword}'"
    
    if total_score >= PERSONAL_SCORE_THRESHOLD:
        return True, reason
    else:
        return False, None


def get_personal_match_details(description: str) -> dict:
    """
    Get detailed match information for debugging/analysis.
    
    Returns:
        {
            "is_personal": bool,
            "matches": [{"keyword": str, "weight": float, "position": int, "ignored": bool, "reason_ignored": str}],
            "total_score": float,
            "top_reason": Optional[str],
        }
    """
    result = {
        "is_personal": False,
        "matches": [],
        "total_score": 0.0,
        "top_reason": None,
    }
    
    if not description or not description.strip():
        return result
    
    matched_keywords: List[Tuple[str, float, int, bool, str]] = []
    
    for keyword in PERSONAL_KEYWORDS:
        pattern = _get_pattern(keyword)
        matches = list(pattern.finditer(description))
        
        for match in matches:
            match_start = match.start()
            ignored = False
            ignore_reason = ""
            
            if has_negation_prefix(description, match_start, keyword):
                ignored = True
                ignore_reason = "negation prefix found"
            elif is_business_context(description, keyword):
                ignored = True
                ignore_reason = "business context"
            
            weight = PERSONAL_KEYWORD_WEIGHTS.get(keyword, 0.7)
            matched_keywords.append((keyword, weight, match_start, ignored, ignore_reason))
    
    all_matches = []
    active_score = 0.0
    
    for kw, weight, pos, ignored, reason_ignored in matched_keywords:
        all_matches.append({
            "keyword": kw,
            "weight": weight,
            "position": pos,
            "ignored": ignored,
            "reason_ignored": reason_ignored,
        })
        if not ignored:
            active_score += weight
    
    result["matches"] = all_matches
    result["total_score"] = active_score
    
    if active_score >= PERSONAL_SCORE_THRESHOLD:
        result["is_personal"] = True
        active_matches = [m for m in matched_keywords if not m[3]]
        if active_matches:
            active_matches.sort(key=lambda x: (-x[1], x[2]))
            result["top_reason"] = f"Personal expense detected (score: {active_score:.1f}) - matched '{active_matches[0][0]}'"
    
    return result
