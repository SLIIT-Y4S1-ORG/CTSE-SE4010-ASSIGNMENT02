"""
ticket_classifier_tool.py
--------------------------
Rule-based tool for classifying customer support tickets.
Uses keyword matching and heuristic logic — NO LLM involved.

Categories : damaged_item | refund_request | billing_issue | shipping_issue
             | technical_issue | account_issue | missing_information | other
Urgency    : low | medium | high
Sentiment  : positive | neutral | negative
"""

from __future__ import annotations

import re
from typing import Dict, List


# ---------------------------------------------------------------------------
# Keyword maps
# ---------------------------------------------------------------------------

CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "damaged_item": [
        "broken", "damaged", "cracked", "shattered", "defective",
        "arrived broken", "smashed", "crushed", "dented", "torn",
        "faulty", "not working", "doesnt work", "doesn't work",
        "malfunctioning", "scratched", "bent",
    ],
    "refund_request": [
        "refund", "money back", "reimburse", "reimbursement",
        "return", "give me back", "charge back", "chargeback",
        "get my money", "want my money",
    ],
    "billing_issue": [
        "charged twice", "double charge", "overcharged", "wrong amount",
        "incorrect charge", "billing error", "invoice", "billed",
        "extra charge", "unexpected charge", "bank statement",
        "payment issue", "duplicate charge",
    ],
    "shipping_issue": [
        "not delivered", "hasn't arrived", "hasn't been delivered",
        "late delivery", "delayed", "missing package", "tracking",
        "shipment", "courier", "shipping", "delivery issue",
        "lost package", "wrong address", "package missing",
        "where is my order", "where's my order",
    ],
    "technical_issue": [
        "doesn't turn on", "won't turn on", "not turning on",
        "error", "crash", "bug", "glitch", "freezing", "frozen",
        "not loading", "connection issue", "can't connect",
        "login error", "won't work", "technical", "software",
        "app", "website down", "page not loading",
    ],
    "account_issue": [
        "can't log in", "cannot log in", "forgot password",
        "reset password", "account locked", "account suspended",
        "account blocked", "account issue", "access denied",
        "unauthorized", "can't access", "cannot access",
        "profile", "account settings",
    ],
}

URGENCY_HIGH_KEYWORDS: List[str] = [
    "urgent", "immediately", "asap", "right now", "emergency",
    "critical", "severe", "worst", "unacceptable", "furious",
    "outraged", "disgusting", "terrible", "horrible", "horrible",
    "already waited", "still waiting", "lawsuit", "legal action",
    "fraud", "scam", "stolen", "threatening",
]

URGENCY_LOW_KEYWORDS: List[str] = [
    "whenever", "no rush", "not urgent", "whenever you can",
    "take your time", "low priority", "minor",
]

NEGATIVE_KEYWORDS: List[str] = [
    "angry", "furious", "upset", "frustrated", "disappointed",
    "terrible", "horrible", "awful", "unacceptable", "ridiculous",
    "worst", "never again", "outraged", "disgraceful", "disgusting",
    "this is a joke", "incompetent", "pathetic", "useless",
    "what the hell", "absolutely ridiculous",
]

POSITIVE_KEYWORDS: List[str] = [
    "thank", "thanks", "appreciate", "grateful", "happy", "pleased",
    "great service", "excellent", "wonderful", "love", "amazing",
    "fantastic", "well done", "good job",
]

# Required fields whose absence signals missing information
MISSING_INFO_CHECKS: Dict[str, List[str]] = {
    "order_id": [
        r"\bord(?:er)?[-\s]?\d+\b",
        r"\b#\d{4,}\b",
        r"\border\s+number\b",
        r"\border\s+id\b",
    ],
    "evidence_attachment": [
        r"\battach(?:ed|ment|ing)\b",
        r"\bphoto\b",
        r"\bpicture\b",
        r"\bscreenshot\b",
        r"\bimage\b",
        r"\breceipt\b",
        r"\bproof\b",
    ],
    "product_details": [
        r"\bmodel\b",
        r"\bserial\b",
        r"\bproduct\s+name\b",
        r"\bitem\s+name\b",
        r"\bsku\b",
    ],
    "account_email": [
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        r"\bemail\b",
        r"\be[\-\s]?mail\s+address\b",
    ],
}

# Categories that specifically require evidence to resolve
EVIDENCE_REQUIRED_CATEGORIES: List[str] = ["damaged_item"]

# Categories that always need an order ID
ORDER_ID_REQUIRED_CATEGORIES: List[str] = [
    "damaged_item",
    "refund_request",
    "billing_issue",
    "shipping_issue",
]

# Categories that always need account email
EMAIL_REQUIRED_CATEGORIES: List[str] = ["account_issue"]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Lowercase, strip punctuation noise, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"['\u2019\u2018]", "", text)  # smart quotes / apostrophes
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _keyword_hits(text: str, keywords: List[str]) -> int:
    """Return count of matching keywords found in *text*."""
    return sum(1 for kw in keywords if kw in text)


def _regex_hits(text: str, patterns: List[str]) -> bool:
    """Return True if any regex pattern matches *text*."""
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_ticket(ticket_text: str) -> Dict[str, object]:
    """
    Classify a customer support ticket using rule-based keyword logic.

    Parameters
    ----------
    ticket_text : str
        The raw text body of the support ticket.

    Returns
    -------
    dict
        A structured classification result with the following keys:

        - ``category``          (str)        : One of the defined categories.
        - ``urgency``           (str)        : ``"low"`` | ``"medium"`` | ``"high"``.
        - ``sentiment``         (str)        : ``"positive"`` | ``"neutral"`` | ``"negative"``.
        - ``missing_information`` (List[str]): List of missing field names.
        - ``confidence``        (str)        : ``"high"`` | ``"medium"`` | ``"low"``
                                               (how confident the rule engine is).

    Raises
    ------
    ValueError
        If *ticket_text* is empty or not a string.
    """
    if not isinstance(ticket_text, str):
        raise ValueError(f"ticket_text must be a str, got {type(ticket_text).__name__}")

    stripped = ticket_text.strip()
    if not stripped:
        raise ValueError("ticket_text must not be empty")

    norm = _normalise(stripped)

    # ------------------------------------------------------------------
    # 1. Category detection — score each category, pick the winner
    # ------------------------------------------------------------------
    scores: Dict[str, int] = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        scores[cat] = _keyword_hits(norm, keywords)

    best_score = max(scores.values())
    if best_score == 0:
        category = "other"
        cat_confidence = "low"
    else:
        # Collect all categories tied at the top score
        top_cats = [c for c, s in scores.items() if s == best_score]
        category = top_cats[0]  # deterministic tie-break: dict insertion order
        cat_confidence = "high" if best_score >= 2 else "medium"

    # ------------------------------------------------------------------
    # 2. Urgency detection
    # ------------------------------------------------------------------
    high_hits = _keyword_hits(norm, URGENCY_HIGH_KEYWORDS)
    low_hits = _keyword_hits(norm, URGENCY_LOW_KEYWORDS)

    if high_hits >= 1:
        urgency = "high"
    elif low_hits >= 1:
        urgency = "low"
    else:
        # Use exclamation marks as a proxy for frustration
        exclamation_count = stripped.count("!")
        urgency = "high" if exclamation_count >= 2 else "medium"

    # ------------------------------------------------------------------
    # 3. Sentiment detection
    # ------------------------------------------------------------------
    neg_hits = _keyword_hits(norm, NEGATIVE_KEYWORDS)
    pos_hits = _keyword_hits(norm, POSITIVE_KEYWORDS)

    if neg_hits > pos_hits:
        sentiment = "negative"
    elif pos_hits > neg_hits:
        sentiment = "positive"
    else:
        # Fallback: exclamation marks + all-caps segments signal frustration
        allcaps_words = len(re.findall(r"\b[A-Z]{3,}\b", stripped))
        sentiment = "negative" if (stripped.count("!") >= 1 or allcaps_words >= 1) else "neutral"

    # ------------------------------------------------------------------
    # 4. Missing information detection
    # ------------------------------------------------------------------
    missing: List[str] = []

    # order_id required for transactional categories
    if category in ORDER_ID_REQUIRED_CATEGORIES:
        has_order = _regex_hits(norm, MISSING_INFO_CHECKS["order_id"])
        if not has_order:
            missing.append("order_id")

    # evidence required for damage claims
    if category in EVIDENCE_REQUIRED_CATEGORIES:
        has_evidence = _regex_hits(norm, MISSING_INFO_CHECKS["evidence_attachment"])
        if not has_evidence:
            missing.append("evidence_attachment")

    # product details — required when the ticket is vague about which item
    has_product = _regex_hits(norm, MISSING_INFO_CHECKS["product_details"])
    word_count = len(norm.split())
    if word_count < 20 and not has_product and category not in ("billing_issue", "account_issue"):
        missing.append("product_details")

    # account email — required for account-related issues
    if category in EMAIL_REQUIRED_CATEGORIES:
        has_email = _regex_hits(norm, MISSING_INFO_CHECKS["account_email"])
        if not has_email:
            missing.append("account_email")

    # ------------------------------------------------------------------
    # 5. Special override: if the ticket itself is gibberish / one-liner
    #    with no actionable content, reclassify as missing_information
    # ------------------------------------------------------------------
    if word_count < 5 and category == "other":
        category = "missing_information"
        missing = ["order_id", "product_details"]
        cat_confidence = "low"

    return {
        "category": category,
        "urgency": urgency,
        "sentiment": sentiment,
        "missing_information": missing,
        "confidence": cat_confidence,
    }
