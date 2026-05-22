from typing import Optional, List, Tuple
from rapidfuzz import fuzz
import re

from app.core.constants import (
    ThresholdConfig,
    DESCRIPTION_VENDOR_PATTERNS,
)


DEFAULT_VENDOR_MAP: dict[str, list[str]] = {
    "Amazon Web Services": [
        "AWS",
        "amazon-web-services",
        "AMAZON WEB SERVICES INC",
    ],
    "Uber": ["UBER INDIA", "uber-business", "Uber Technologies"],
    "Swiggy": ["swiggy for business", "SWIGGY"],
    "Zoom": ["ZOOM VIDEO COMMUNICATIONS", "zoom.us"],
    "Notion": ["notion.so", "NOTION LABS"],
    "Salesforce": ["SALESFORCE INC", "salesforce.com"],
    "Adobe": ["ADOBE SYSTEMS", "adobe.com"],
    "Razorpay": ["RAZORPAY SOFTWARE PVT LTD"],
    "Flipkart": ["FLIPKART INTERNET PVT LTD"],
    "IndiGo": ["INDIGO AIRLINES", "InterGlobe Aviation"],
}


def _has_vendor_negation(text: str, match_start: int, matched_text: str) -> bool:
    """
    Check if a vendor match is specifically negated.
    Only negates if "not [vendor]" or similar pattern is DIRECTLY associated with the match.
    Example: "Not AWS but Azure" should negate AWS but NOT Azure.
    """
    text_lower = text.lower()
    matched_lower = matched_text.lower()
    
    match_end = match_start + len(matched_text)
    search_start = max(0, match_start - 50)
    search_end = min(len(text_lower), match_end + 30)
    search_context = text_lower[search_start:search_end]
    
    negation_pattern = re.compile(
        r'\b(not|no)\b(?:\s+(?:a|an|the))?\s+' + re.escape(matched_lower) + r'\b',
        re.IGNORECASE
    )
    
    if negation_pattern.search(search_context):
        relative_pos = match_start - search_start
        pattern_matches = list(negation_pattern.finditer(search_context))
        
        for pm in pattern_matches:
            if pm.end() <= relative_pos + 5:
                later_context = search_context[pm.end():]
                if "but" in later_context or "rather" in later_context or "instead" in later_context:
                    if "professional" in later_context or "business" in later_context:
                        pass
                return True
    
    direct_negations = [
        f"not {matched_lower}",
        f"no {matched_lower}",
    ]
    
    for neg in direct_negations:
        if neg in search_context:
            neg_pos = search_context.find(neg)
            if neg_pos >= 0 and neg_pos <= match_start - search_start + 10:
                return True
    
    return False


class VendorResolver:
    def __init__(self, vendor_map: Optional[dict[str, list[str]]] = None):
        self.vendor_map = vendor_map or DEFAULT_VENDOR_MAP
        self._alias_to_canonical: dict[str, str] = {}
        for canonical, aliases in self.vendor_map.items():
            for alias in aliases:
                self._alias_to_canonical[alias.lower()] = canonical
        self._canonical_names = list(self.vendor_map.keys())

    def resolve_vendor(
        self, vendor_raw: str, description: str = ""
    ) -> tuple[str, str, Optional[str]]:
        if not vendor_raw or not vendor_raw.strip():
            return self._infer_from_description(description)

        vendor_stripped = vendor_raw.strip()

        exact_lower = vendor_stripped.lower()
        if exact_lower in self._alias_to_canonical:
            canonical = self._alias_to_canonical[exact_lower]
            return canonical, vendor_stripped, None

        best_canonical: Optional[str] = None
        best_alias: Optional[str] = None
        best_score = 0.0

        for canonical, aliases in self.vendor_map.items():
            for alias in aliases:
                score = (
                    fuzz.token_set_ratio(
                        vendor_stripped.lower(), alias.lower()
                    )
                    / 100.0
                )
                if score > best_score:
                    best_score = score
                    best_canonical = canonical
                    best_alias = alias

        if best_canonical is not None and best_score >= ThresholdConfig.VENDOR_MATCH_THRESHOLD:
            return best_canonical, best_alias, None

        return vendor_stripped, vendor_stripped, "UNKNOWN_VENDOR"

    def _infer_from_description(
        self, description: str
    ) -> tuple[str, str, Optional[str]]:
        """
        Infer vendor from description using:
        1. Regex patterns with word boundaries (avoids false positives)
        2. Smart negation handling (for "Not AWS but Azure" patterns)
        3. Scoring based on number of pattern matches
        """
        if not description or not description.strip():
            return "Unknown", "Unknown", "UNKNOWN_VENDOR"
        
        matches: List[Tuple[str, int, int]] = []
        
        for vendor, patterns in DESCRIPTION_VENDOR_PATTERNS.items():
            vendor_match_count = 0
            first_match_pos = len(description)
            
            for pattern in patterns:
                found_matches = list(pattern.finditer(description))
                
                for match in found_matches:
                    match_start = match.start()
                    matched_text = match.group()
                    
                    if _has_vendor_negation(description, match_start, matched_text):
                        continue
                    
                    vendor_match_count += 1
                    if match_start < first_match_pos:
                        first_match_pos = match_start
            
            if vendor_match_count > 0:
                matches.append((vendor, vendor_match_count, first_match_pos))
        
        if not matches:
            return "Unknown", "Unknown", "UNKNOWN_VENDOR"
        
        matches.sort(key=lambda x: (-x[1], x[2]))
        
        best_vendor = matches[0][0]
        
        return best_vendor, best_vendor, None


_resolver_instance = None


def _get_resolver():
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = VendorResolver()
    return _resolver_instance


def resolve_vendor(vendor_raw: str, description: str = "") -> tuple[str, str, Optional[str]]:
    return _get_resolver().resolve_vendor(vendor_raw, description)
