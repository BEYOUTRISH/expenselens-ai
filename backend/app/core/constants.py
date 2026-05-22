"""
Shared Constants & Configuration for ExpenseLens

Centralizes all hardcoded thresholds, keywords, rates, and settings
that were previously duplicated across multiple files.
"""

import re
from typing import Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

PERSONAL_KEYWORDS: list[str] = [
    "personal", "spouse", "gift", "birthday", "home", "grocery",
    "mediclaim", "amazon prime", "home account", "personal travel",
    "family", "wife", "husband", "son", "daughter",
]


PERSONAL_KEYWORD_WEIGHTS: dict[str, float] = {
    "personal": 1.0,
    "personal travel": 1.0,
    "spouse": 1.0,
    "wife": 1.0,
    "husband": 1.0,
    "son": 0.8,
    "daughter": 0.8,
    "family": 0.8,
    "home account": 1.0,
    "home": 0.7,
    "gift": 0.9,
    "birthday": 0.9,
    "grocery": 0.7,
    "mediclaim": 0.9,
    "amazon prime": 0.8,
}


PERSONAL_KEYWORD_CATEGORIES: dict[str, str] = {
    "personal": "General Personal",
    "personal travel": "General Personal",
    "spouse": "Family & Relations",
    "wife": "Family & Relations",
    "husband": "Family & Relations",
    "son": "Family & Relations",
    "daughter": "Family & Relations",
    "family": "Family & Relations",
    "home": "Household Expenses",
    "home account": "Household Expenses",
    "grocery": "Household Expenses",
    "gift": "Personal Occasions",
    "birthday": "Personal Occasions",
    "mediclaim": "Personal Healthcare",
    "amazon prime": "Personal Subscriptions",
}


PERSONAL_CATEGORY_COLORS: dict[str, str] = {
    "Family & Relations": "#ef4444",
    "Household Expenses": "#f97316",
    "Personal Occasions": "#eab308",
    "General Personal": "#8b5cf6",
    "Personal Healthcare": "#06b6d4",
    "Personal Subscriptions": "#ec4899",
}


PERSONAL_CATEGORY_RISKS: dict[str, list[str]] = {
    "Family & Relations": [
        "Indicates potential personal use of corporate funds by employees",
        "Family-related charges suggest policy awareness gaps",
        "May indicate shared card misuse with family members",
    ],
    "Household Expenses": [
        "Home-related charges blur personal/business expense boundaries",
        "Employees may be unclear about reimbursable vs non-reimbursable",
        "Groceries and home supplies typically indicate personal card use",
    ],
    "Personal Occasions": [
        "Gift and birthday expenses need clear policy limits",
        "May be legitimate client gifts or personal - requires review",
        "Unclear gift policies lead to inconsistent expense reporting",
    ],
    "General Personal": [
        "Explicit 'personal' markers indicate clear policy violations",
        "Personal travel charged to company requires immediate follow-up",
        "Suggests either card misuse or policy misunderstanding",
    ],
    "Personal Healthcare": [
        "Mediclaim charges may indicate health insurance premiums paid via corporate card",
        "May be legitimate if part of employee benefits package",
        "Requires review against company health benefit policies",
    ],
    "Personal Subscriptions": [
        "Personal subscriptions like Amazon Prime often indicate card sharing",
        "Employees may not realize personal subscriptions are non-reimbursable",
        "Multiple personal subscriptions suggest systematic card misuse",
    ],
}


PERSONAL_CATEGORY_SOLUTIONS: dict[str, list[dict]] = {
    "Family & Relations": [
        {
            "action": "Policy Review & Communication",
            "priority": "HIGH",
            "description": "Review and explicitly communicate expense policy regarding family-related charges",
        },
        {
            "action": "Cardholder Training",
            "priority": "MEDIUM",
            "description": "Provide targeted training on distinguishing personal vs business expenses",
        },
        {
            "action": "Audit Follow-up",
            "priority": "HIGH",
            "description": "Identify employees with frequent family charges and conduct review meetings",
        },
    ],
    "Household Expenses": [
        {
            "action": "Clarify Reimbursable Expenses",
            "priority": "HIGH",
            "description": "Create clear guidelines on what qualifies as reimbursable work-from-home expenses",
        },
        {
            "action": "Home Office Policy",
            "priority": "MEDIUM",
            "description": "Update home office expense policy with specific allowed/disallowed items",
        },
        {
            "action": "Regular Policy Reminders",
            "priority": "MEDIUM",
            "description": "Send monthly policy reminders to all cardholders",
        },
    ],
    "Personal Occasions": [
        {
            "action": "Gift Policy Update",
            "priority": "HIGH",
            "description": "Create clear gift policy with dollar limits and approval requirements",
        },
        {
            "action": "Client Gift vs Personal Gift",
            "priority": "MEDIUM",
            "description": "Train employees to document business purpose for all gift purchases",
        },
        {
            "action": "Pre-approval Requirement",
            "priority": "MEDIUM",
            "description": "Implement pre-approval requirement for gifts above a certain threshold",
        },
    ],
    "General Personal": [
        {
            "action": "Immediate Review",
            "priority": "CRITICAL",
            "description": "Explicitly marked 'personal' expenses require immediate manager review",
        },
        {
            "action": "Card Recovery Protocol",
            "priority": "HIGH",
            "description": "Consider card suspension or recovery for repeated personal charges",
        },
        {
            "action": "Policy Acknowledgment",
            "priority": "MEDIUM",
            "description": "Require written policy acknowledgment from employees with personal charges",
        },
    ],
    "Personal Healthcare": [
        {
            "action": "Benefits Review",
            "priority": "MEDIUM",
            "description": "Review whether mediclaim charges are part of authorized employee benefits",
        },
        {
            "action": "Clarify Health Policy",
            "priority": "MEDIUM",
            "description": "Update policy on what medical-related expenses are reimbursable",
        },
        {
            "action": "Benefit Enrollment Audit",
            "priority": "LOW",
            "description": "Verify if employees with mediclaim charges are enrolled in benefit programs",
        },
    ],
    "Personal Subscriptions": [
        {
            "action": "Subscription Audit",
            "priority": "HIGH",
            "description": "Identify and cancel personal subscriptions charged to corporate cards",
        },
        {
            "action": "Business Subscription Policy",
            "priority": "MEDIUM",
            "description": "Create approved list of business software subscriptions",
        },
        {
            "action": "Card Statement Review",
            "priority": "MEDIUM",
            "description": "Implement monthly statement reviews to catch recurring personal subscriptions",
        },
    ],
}


PERSONAL_EXPENSE_OVERALL_RISKS: list[str] = [
    "Personal expenses increase operational costs and reduce profitability",
    "Unreimbursed personal charges may create tax compliance issues",
    "Frequent personal expenses indicate weak internal controls",
    "Policy violations can lead to employee morale issues and audit findings",
    "Shared card usage increases fraud risk",
]


PERSONAL_EXPENSE_OVERALL_SOLUTIONS: list[dict] = [
    {
        "action": "Expense Policy Refresh",
        "priority": "HIGH",
        "description": "Update and communicate a comprehensive expense policy with clear examples",
    },
    {
        "action": "Manager Training",
        "priority": "MEDIUM",
        "description": "Train managers on expense review best practices and red flag identification",
    },
    {
        "action": "Automated Detection",
        "priority": "MEDIUM",
        "description": "Leverage ExpenseLens personal expense detection in regular review workflows",
    },
    {
        "action": "Regular Audits",
        "priority": "HIGH",
        "description": "Schedule periodic expense audits focused on high-risk categories and employees",
    },
]


NEGATION_TERMS: list[str] = [
    "not personal", "not a personal", "non personal", "non-personal",
    "office", "company", "business", "corporate", "official",
    "for business", "for office", "for company", "for team", "for client",
    "team lunch", "team dinner", "team event",
    "client lunch", "client dinner", "client meeting",
    "business travel", "business trip",
    "office gift", "company gift", "corporate gift",
    "excluding", "not including",
]


NEGATION_PREFIX_PATTERN = re.compile(
    r'\b(not|non|non-|excluding|never|no)\s+(personal|business|office|company|corporate)?',
    re.IGNORECASE
)


def create_word_boundary_pattern(keyword: str) -> re.Pattern:
    """
    Create a regex pattern with word boundaries for a keyword.
    Handles multi-word keywords and special characters.
    """
    parts = keyword.split()
    if len(parts) > 1:
        escaped_parts = [re.escape(p) for p in parts]
        pattern = r'\b' + r'\s+'.join(escaped_parts) + r'\b'
    else:
        escaped = re.escape(keyword)
        pattern = rf'\b{escaped}\b'
    
    return re.compile(pattern, re.IGNORECASE)


BUSINESS_CONTEXT_PATTERNS = [
    "home office",
    "office supplies",
    "office equipment",
    "office furniture",
    "business gift",
    "company gift",
    "corporate gift",
    "office gift",
]


def has_negation_prefix(text: str, match_start: int, keyword: Optional[str] = None) -> bool:
    """
    Check if there's a negation term within a reasonable distance before the match.
    Returns True if negation found (meaning the match should be ignored).
    
    Args:
        text: The full text being searched
        match_start: Start position of the matched keyword
        keyword: The actual keyword that was matched (optional, for smarter detection)
    """
    text_lower = text.lower()
    
    wider_context_start = max(0, match_start - 60)
    wider_context = text_lower[wider_context_start:match_start]
    
    if keyword:
        keyword_lower = keyword.lower()
        
        not_pattern = re.compile(r'\bnot\b(?:\s+\w+){0,3}\s+' + re.escape(keyword_lower) + r'\b')
        if not_pattern.search(wider_context):
            later_context = text_lower[match_start:match_start + 80]
            if "but" in later_context and (
                "not" in later_context.lower().split("but")[1] if "but" in later_context else False or
                "rather" in later_context or "instead" in later_context or "professional" in later_context
            ):
                return True
            else:
                return True
        
        direct_patterns = [
            f"not {keyword_lower}",
            f"not a {keyword_lower}",
            f"not the {keyword_lower}",
            f"no {keyword_lower}",
            f"non-{keyword_lower}",
        ]
        
        for pattern in direct_patterns:
            if pattern in wider_context:
                return True
    
    if keyword and keyword_lower in ["personal", "gift", "home", "grocery", "family", "spouse", "wife", "husband", "son", "daughter", "birthday", "mediclaim"]:
        if "not" in wider_context:
            later_context = text_lower[match_start:match_start + 80]
            if "but" in later_context:
                after_but = later_context.split("but", 1)[1] if "but" in later_context else ""
                if "professional" in after_but or "business" in after_but or "work" in after_but:
                    return True
            else:
                return True
    
    strong_negations = [
        "for business", "for office", "for company", "for team", "for client",
        "team lunch", "team dinner", "client lunch", "client dinner",
        "business travel", "official business",
    ]
    
    for indicator in strong_negations:
        if indicator in wider_context:
            return True
    
    if "home office" in text_lower:
        return False
    
    weak_negations = ["office", "company", "business", "corporate", "official"]
    for indicator in weak_negations:
        if indicator in wider_context:
            if "home" in wider_context:
                pass
            else:
                return True
    
    return False


def is_business_context(text: str, keyword: str) -> bool:
    """
    Check if the keyword is used in a business context (should not be flagged as personal).
    """
    text_lower = text.lower()
    keyword_lower = keyword.lower()
    
    if keyword_lower == "home":
        for pattern in BUSINESS_CONTEXT_PATTERNS:
            if pattern in text_lower:
                return True
    
    if keyword_lower == "gift":
        if any(pattern in text_lower for pattern in ["business gift", "company gift", "corporate gift", "office gift", "client gift"]):
            return True
    
    if keyword_lower in ["grocery", "grocery shopping"]:
        if any(pattern in text_lower for pattern in ["team lunch", "team dinner", "office lunch", "office dinner", "client lunch", "client dinner"]):
            return True
    
    return False


DESCRIPTION_VENDOR_PATTERNS: dict[str, list[re.Pattern]] = {}


def _compile_vendor_patterns():
    """Compile vendor patterns with word boundaries."""
    global DESCRIPTION_VENDOR_PATTERNS
    
    raw_patterns: dict[str, list[str]] = {
        "Amazon Web Services": [
            r'\baws\b', r'\bec2\b', r'\bcloudfront\b', r'\bs3\b',
            r'\bamazon\s+web\s+services\b',
        ],
        "Uber": [
            r'\buber\b', r'\bcab\b', r'\bride\b',
        ],
        "Swiggy": [
            r'\bswiggy\b', r'\bfood\s+delivery\b',
        ],
        "Zoom": [
            r'\bzoom\b', r'\bvideo\s+call\b',
        ],
        "Notion": [
            r'\bnotion\b',
        ],
        "Salesforce": [
            r'\bsalesforce\b',
        ],
        "Adobe": [
            r'\badobe\b',
        ],
        "Razorpay": [
            r'\brazorpay\b', r'\bpayment\s+gateway\b',
        ],
        "Flipkart": [
            r'\bflipkart\b',
        ],
        "IndiGo": [
            r'\bindigo\b', r'\bflight\b', r'\bairline\b',
        ],
        "Microsoft Azure": [
            r'\bmicrosoft\b', r'\bazure\b',
        ],
        "Google Cloud India": [
            r'\bgoogle\b', r'\bgcp\b',
        ],
    }
    
    DESCRIPTION_VENDOR_PATTERNS = {}
    for vendor, patterns in raw_patterns.items():
        DESCRIPTION_VENDOR_PATTERNS[vendor] = [
            re.compile(p, re.IGNORECASE) for p in patterns
        ]


_compile_vendor_patterns()

SENTINEL_VALUES: set[str] = {
    "tbd", "n/a", "na", "--", "nil", "none", "", "null",
}

DEFAULT_EXCHANGE_RATES: dict[str, float] = {
    "USD": 83.5,
    "EUR": 91.2,
    "GBP": 106.4,
    "SGD": 62.3,
    "AED": 22.73,
    "INR": 1.0,
}

CURRENCY_SYMBOLS: dict[str, str] = {
    "₹": "INR",
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
}

CURRENCY_CODES: set[str] = {"USD", "EUR", "GBP", "SGD", "AED", "INR"}

CANONICAL_DEPARTMENTS: list[str] = [
    "Engineering", "Sales", "Product", "Operations", "Finance",
    "IT", "Human Resources", "Marketing", "Legal", "Customer Success",
    "Design", "Research", "Data Science", "DevOps", "QA",
    "Security", "Business Development", "Support", "Training", "Facilities",
]

CANONICAL_VENDORS: dict[str, list[str]] = {
    "AMAZON": ["amazon", "amazon.in", "amazon india", "aws", "amazon web services"],
    "FLIPKART": ["flipkart", "flipkart.com"],
    "SWIGGY": ["swiggy", "swiggy.in", "swiggy genie"],
    "ZOMATO": ["zomato", "zomato.com"],
    "UBER": ["uber", "uber india", "uber eats"],
    "OLA": ["ola", "ola cabs", "ola electric"],
    "GOOGLE": ["google", "google india", "gcp", "google cloud"],
    "MICROSOFT": ["microsoft", "msft", "azure"],
    "DELL": ["dell", "dell technologies"],
    "LENOVO": ["lenovo", "thinkpad"],
}

DATE_PATTERNS: list[tuple[str, str]] = [
    (r"^\d{4}-\d{2}-\d{2}$", "ISO_DATE"),
    (r"^\d{4}/\d{2}/\d{2}$", "ISO_DATE_SLASH"),
    (r"^\d{2}/\d{2}/\d{4}$", "US_DATE"),
    (r"^\d{1,2}/\d{1,2}/\d{4}$", "US_DATE_SHORT"),
    (r"^\d{2}\.\d{2}\.\d{4}$", "EU_DATE_DOT"),
    (r"^\d{2}-\d{2}-\d{4}$", "EU_DATE_DASH"),
    (r"^\d{2}-[A-Za-z]{3}-\d{4}$", "DD_MON_YYYY"),
    (r"^\d{2} [A-Za-z]+ \d{4}$", "DD_MONTH_YYYY"),
    (r"^\d{8}$", "YYYYMMDD"),
]

STANDARD_COLUMNS: list[str] = [
    "txn_id", "submission_date", "txn_date", "amount_raw",
    "currency_raw", "vendor_raw", "description", "department",
    "cost_center", "submitted_by", "receipt_attached", "notes",
]

CANONICAL_SCHEMA_FIELDS: list[str] = [
    "txn_id", "submission_date", "txn_date", "amount_raw",
    "currency_raw", "vendor_raw", "description", "department",
    "cost_center", "submitted_by", "receipt_attached",
]


class ComplianceConfig:
    RECEIPT_WEIGHT: float = 50.0
    ANOMALY_WEIGHT: float = 30.0
    DUPLICATE_WEIGHT: float = 20.0
    PERSONAL_WEIGHT: float = 10.0


class ThresholdConfig:
    ANOMALY_ZSCORE: float = 3.0
    ANOMALY_IQR_MULTIPLIER: float = 1.5
    ISOLATION_FOREST_CONTAMINATION: float = 0.05
    ROUND_NUMBER_MODULUS: float = 10000.0
    ROUND_NUMBER_MIN_AMOUNT: float = 50000.0
    RECEIPT_THRESHOLD: float = 5000.0
    SCHEMA_MATCH_THRESHOLD: float = 0.60
    VENDOR_MATCH_THRESHOLD: float = 0.80
    DEPARTMENT_MATCH_THRESHOLD: float = 0.60
    DUPLICATE_DAYS_WINDOW: int = 3
    DUPLICATE_DESC_SIMILARITY: float = 0.85


class AnomalyWeights:
    ZSCORE: float = 0.30
    IQR: float = 0.25
    ISOLATION_FOREST: float = 0.30
    ROUND_NUMBER: float = 0.15
    WEEKEND: float = 0.10


class RuntimeSettings:
    _instance: Optional["RuntimeSettings"] = None
    _settings: dict[str, Any] = {
        "base_currency": "INR",
        "exchange_rates": DEFAULT_EXCHANGE_RATES.copy(),
        "departments": CANONICAL_DEPARTMENTS.copy(),
        "vendors": {},
        "openai_key_configured": False,
        "receipt_threshold": ThresholdConfig.RECEIPT_THRESHOLD,
        "anomaly_threshold_zscore": ThresholdConfig.ANOMALY_ZSCORE,
        "ai_provider": "none",
    }

    def __new__(cls) -> "RuntimeSettings":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        return cls._settings.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        cls._settings[key] = value

    @classmethod
    def get_all(cls) -> dict[str, Any]:
        return cls._settings.copy()

    @classmethod
    def update(cls, updates: dict[str, Any]) -> None:
        cls._settings.update(updates)

    @classmethod
    def get_exchange_rate(cls, currency: str) -> float:
        rates = cls._settings.get("exchange_rates", DEFAULT_EXCHANGE_RATES)
        return rates.get(currency.upper(), DEFAULT_EXCHANGE_RATES.get(currency.upper(), 1.0))

    @classmethod
    def get_anomaly_zscore_threshold(cls) -> float:
        return float(cls._settings.get("anomaly_threshold_zscore", ThresholdConfig.ANOMALY_ZSCORE))

    @classmethod
    def get_receipt_threshold(cls) -> float:
        return float(cls._settings.get("receipt_threshold", ThresholdConfig.RECEIPT_THRESHOLD))


def compute_compliance_score(
    df: pd.DataFrame,
    receipt_weight: float = ComplianceConfig.RECEIPT_WEIGHT,
    anomaly_weight: float = ComplianceConfig.ANOMALY_WEIGHT,
    duplicate_weight: float = ComplianceConfig.DUPLICATE_WEIGHT,
    personal_weight: float = ComplianceConfig.PERSONAL_WEIGHT,
) -> dict[str, Any]:
    """
    Centralized compliance score calculation.
    
    Returns a dict with:
        - score: Overall compliance score (0-100)
        - breakdown: Dict with individual component scores
        - metrics: Raw metrics used in calculation
    """
    total_rows = len(df)
    
    if total_rows == 0:
        return {
            "score": 100.0,
            "breakdown": {
                "receipt": 100.0,
                "anomaly": 100.0,
                "duplicate": 100.0,
                "personal": 100.0,
            },
            "metrics": {
                "total_rows": 0,
                "missing_receipts": 0,
                "anomalies": 0,
                "duplicates": 0,
                "personal": 0,
            }
        }
    
    no_receipt = 0
    if "receipt_attached" in df.columns:
        no_receipt = int((df["receipt_attached"] == False).sum())
    
    anomaly_count = 0
    if "is_flagged" in df.columns:
        anomaly_count = int(df["is_flagged"].sum())
    
    duplicate_count = 0
    if "is_duplicate" in df.columns:
        duplicate_count = int(df["is_duplicate"].sum())
    
    personal_count = 0
    if "is_personal" in df.columns:
        personal_count = int(df["is_personal"].sum())
    
    total_weight = receipt_weight + anomaly_weight + duplicate_weight + personal_weight
    receipt_penalty = (no_receipt / total_rows) * (receipt_weight / total_weight * 100)
    anomaly_penalty = (anomaly_count / total_rows) * (anomaly_weight / total_weight * 100)
    duplicate_penalty = (duplicate_count / total_rows) * (duplicate_weight / total_weight * 100)
    personal_penalty = (personal_count / total_rows) * (personal_weight / total_weight * 100)
    
    score = round(100.0 - receipt_penalty - anomaly_penalty - duplicate_penalty - personal_penalty, 1)
    score = max(0.0, min(100.0, score))
    
    return {
        "score": score,
        "breakdown": {
            "receipt": round(100.0 - (no_receipt / total_rows * 100), 1) if total_rows > 0 else 100.0,
            "anomaly": round(100.0 - (anomaly_count / total_rows * 100), 1) if total_rows > 0 else 100.0,
            "duplicate": round(100.0 - (duplicate_count / total_rows * 100), 1) if total_rows > 0 else 100.0,
            "personal": round(100.0 - (personal_count / total_rows * 100), 1) if total_rows > 0 else 100.0,
        },
        "metrics": {
            "total_rows": total_rows,
            "missing_receipts": no_receipt,
            "anomalies": anomaly_count,
            "duplicates": duplicate_count,
            "personal": personal_count,
        }
    }


def compute_employee_compliance(
    df: pd.DataFrame,
    employee_id: str,
    submitted_by_col: str = "submitted_by",
) -> float:
    """
    Compute compliance score for a specific employee.
    Returns 0-100 score.
    """
    if submitted_by_col not in df.columns:
        return 100.0
    
    emp_data = df[df[submitted_by_col] == employee_id]
    if len(emp_data) == 0:
        return 100.0
    
    result = compute_compliance_score(emp_data)
    return result["score"]
