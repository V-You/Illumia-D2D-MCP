"""Cross-sell trigger map and lead detection.

Scans structured discovery notes for phrases that indicate cross-sell
opportunities for Illumia product lines beyond Quickcharge.
"""

from __future__ import annotations

import re
from typing import Any


# -- trigger definitions -------------------------------------------------------

CROSS_SELL_TRIGGERS: list[dict[str, Any]] = [
    # Category A: Mobile ID Readiness (Campus ID team)
    {
        "category": "mobile_id",
        "product_line": "Campus ID",
        "product_name": "Transact Mobile Credential",
        "product_url": "https://www.transactcampus.com/solutions/campus-id/transact-mobile-credential",
        "lead_type": "Hardware Compatibility Report",
        "patterns": [
            re.compile(r"physical\s*(?:prox(?:imity)?)?\s*cards?", re.IGNORECASE),
            re.compile(r"prox(?:imity)?\s*(?:cards?|readers?)", re.IGNORECASE),
            re.compile(r"badge\s*(?:readers?|system)?", re.IGNORECASE),
            re.compile(r"hands[- ]free", re.IGNORECASE),
            re.compile(r"contactless\s*(?:entry|access)", re.IGNORECASE),
            re.compile(r"apple\s*wallet", re.IGNORECASE),
            re.compile(r"google\s*wallet", re.IGNORECASE),
            re.compile(r"samsung\s*wallet", re.IGNORECASE),
        ],
        "gap_analysis_template": (
            "Current access hardware uses {trigger_context}. "
            "Transact Mobile Credential (85% market share) puts IDs into "
            "Apple, Google, and Samsung Wallets. Gap: assess NFC reader "
            "compatibility and provisioning requirements for mobile credential rollout."
        ),
        "recommended_action": (
            "Connect with Campus ID team for a hardware compatibility "
            "assessment and Mobile Credential pilot proposal."
        ),
    },
    # Category B: Unified Insights (Campus Commerce team)
    {
        "category": "unified_insights",
        "product_line": "Campus Commerce",
        "product_name": "Transact Insights",
        "product_url": "https://www.transactcampus.com/solutions/campus-commerce/transact-insights-for-campus-commerce",
        "lead_type": "Data Silo Map",
        "patterns": [
            re.compile(r"separate\s*(?:reporting|pos|system|vendor)", re.IGNORECASE),
            re.compile(r"different\s*(?:reporting|pos|system|vendor)", re.IGNORECASE),
            re.compile(r"reconciliation\s*(?:is\s+)?(?:a\s+)?(?:nightmare|difficult|hard|painful)", re.IGNORECASE),
            re.compile(r"fragmented", re.IGNORECASE),
            re.compile(r"multiple\s*(?:systems|vendors|pos)", re.IGNORECASE),
            re.compile(r"can'?t\s+see\s+real[- ]?time", re.IGNORECASE),
            re.compile(r"manual\s*reconcil", re.IGNORECASE),
        ],
        "gap_analysis_template": (
            "Client reports '{trigger_context}' -- indicating fragmented data "
            "across locations. Transact Insights centralizes all transaction "
            "data for real-time foot traffic, spend analytics, and tax "
            "compliance reporting."
        ),
        "recommended_action": (
            "Connect with Campus Commerce team for a data consolidation "
            "assessment and Transact Insights demo."
        ),
    },
    # Category C: Sponsor Payments (Integrated Payments team)
    {
        "category": "sponsor_payments",
        "product_line": "Integrated Payments",
        "product_name": "Transact Sponsor Payments",
        "product_url": "https://transactcampus.com/resources/solution-briefs/transact-sponsor-payments",
        "lead_type": "Manual Overhead Estimate",
        "patterns": [
            re.compile(r"subsidiz", re.IGNORECASE),
            re.compile(r"third[- ]party\s*pay", re.IGNORECASE),
            re.compile(r"employer\s*pays", re.IGNORECASE),
            re.compile(r"government\s*agency", re.IGNORECASE),
            re.compile(r"manual\s*billing|billed?\s*manually", re.IGNORECASE),
            re.compile(r"excel\s*(?:spreadsheet|billing|tracking)", re.IGNORECASE),
            re.compile(r"nursing\s*(?:school|college|program|student)", re.IGNORECASE),
            re.compile(r"bulk\s*payment", re.IGNORECASE),
        ],
        "gap_analysis_template": (
            "Client describes '{trigger_context}' -- indicating manual "
            "third-party billing workflows. Transact Sponsor Payments "
            "automates B2B billing for employers, government agencies, "
            "and educational partners."
        ),
        "recommended_action": (
            "Connect with Integrated Payments team for a manual overhead "
            "calculation and Sponsor Payments portal demo."
        ),
    },
]


def detect_leads(parsed_notes: dict[str, Any]) -> list[dict[str, Any]]:
    """Scan parsed notes for cross-sell triggers.

    Returns a list of leads, each with the trigger quote, product info,
    gap analysis, and recommended action.
    """
    leads: list[dict[str, Any]] = []
    text_blob = _build_text_blob(parsed_notes)
    detected_categories: set[str] = set()

    for trigger_def in CROSS_SELL_TRIGGERS:
        if trigger_def["category"] in detected_categories:
            continue

        for pattern in trigger_def["patterns"]:
            m = pattern.search(text_blob)
            if m:
                trigger_context = m.group(0).strip()

                # find original source quote from parsed notes
                source_quote = _find_source_quote(parsed_notes, trigger_context)

                leads.append({
                    "trigger_quote": source_quote or trigger_context,
                    "product_line": trigger_def["product_line"],
                    "product_name": trigger_def["product_name"],
                    "product_url": trigger_def["product_url"],
                    "lead_type": trigger_def["lead_type"],
                    "gap_analysis": trigger_def["gap_analysis_template"].format(
                        trigger_context=trigger_context,
                    ),
                    "recommended_action": trigger_def["recommended_action"],
                })
                detected_categories.add(trigger_def["category"])
                break

    return leads


def _build_text_blob(parsed_notes: dict[str, Any]) -> str:
    """Combine all text from parsed notes into a single string."""
    parts: list[str] = []
    for key in ("locations", "hardware", "payment_methods", "integrations", "pain_points"):
        for item in parsed_notes.get(key, []):
            parts.append(item.get("source_quote", ""))
            parts.append(item.get("text", ""))
            parts.append(item.get("item", ""))
            parts.append(item.get("context", ""))
            parts.append(item.get("method", ""))
            parts.append(item.get("system", ""))
            parts.append(item.get("name", ""))
    return " ".join(parts)


def _find_source_quote(parsed_notes: dict[str, Any], trigger: str) -> str | None:
    """Find the original source quote containing the trigger text."""
    trigger_lower = trigger.lower()
    for key in ("hardware", "pain_points", "payment_methods", "integrations", "locations"):
        for item in parsed_notes.get(key, []):
            quote = item.get("source_quote", "") or item.get("text", "")
            if trigger_lower in quote.lower():
                return quote
    return None
