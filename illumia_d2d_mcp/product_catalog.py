"""Bundled Quickcharge/Transact product catalog with realistic mock data.

All data is from publicly available Transact/CBORD product pages.
"""

from __future__ import annotations

from typing import Any


PRODUCTS: list[dict[str, Any]] = [
    # -- Point of Sale --
    {
        "name": "Quickcharge POS Terminal",
        "sku": "QC-POS-100",
        "category": "hardware",
        "subcategory": "point_of_sale",
        "description": "Countertop POS terminal for campus dining and retail with campus card, credit/debit, and mobile payment support",
        "dependencies": ["Quickcharge Server", "Network infrastructure"],
        "triggers": ["register", "pos", "terminal", "checkout", "counter", "cashier"],
    },
    {
        "name": "Quickcharge Self-Service Kiosk",
        "sku": "QC-KIOSK-200",
        "category": "hardware",
        "subcategory": "point_of_sale",
        "description": "Self-service ordering and payment kiosk for high-traffic dining locations",
        "dependencies": ["Quickcharge Server", "Network infrastructure"],
        "triggers": ["kiosk", "self-service", "self service", "unattended"],
    },
    {
        "name": "Account Funding Terminal",
        "sku": "QC-AFT-800",
        "category": "hardware",
        "subcategory": "point_of_sale",
        "description": "Terminal for adding funds to campus card accounts via cash, check, or credit/debit",
        "dependencies": ["Quickcharge Server", "Payment processor"],
        "triggers": ["add funds", "funding", "deposit", "load money", "top up"],
    },
    # -- Mobile --
    {
        "name": "Transact Mobile Ordering",
        "sku": "TM-MOB-400",
        "category": "software",
        "subcategory": "mobile",
        "description": "Mobile ordering module for campus dining -- order ahead, skip the line",
        "dependencies": ["Quickcharge Server", "Transact Mobile App"],
        "triggers": ["mobile ordering", "order ahead", "mobile order", "app ordering", "skip the line"],
    },
    {
        "name": "Transact Mobile App",
        "sku": "TM-APP-410",
        "category": "software",
        "subcategory": "mobile",
        "description": "Student/staff mobile app for meal plan balance, adding funds, and mobile payments",
        "dependencies": ["Quickcharge Server"],
        "triggers": ["mobile app", "app", "meal plan balance", "mobile payment"],
    },
    # -- Payment Types --
    {
        "name": "Payroll Deduct Module",
        "sku": "QC-PAY-510",
        "category": "software",
        "subcategory": "payment_type",
        "description": "Payroll deduction for employee campus dining -- charges deducted directly from paycheck",
        "dependencies": ["Quickcharge Server", "Payroll/ERP Connector"],
        "triggers": ["payroll deduct", "payroll deduction", "paycheck", "salary deduct"],
    },
    {
        "name": "Meal Plan Management",
        "sku": "QC-MP-520",
        "category": "software",
        "subcategory": "payment_type",
        "description": "Meal plan administration -- swipes, declining balance, flex dollars",
        "dependencies": ["Quickcharge Server"],
        "triggers": ["meal plan", "swipe", "flex dollars", "declining balance", "board plan"],
    },
    {
        "name": "Campus Card Payment",
        "sku": "QC-CC-530",
        "category": "software",
        "subcategory": "payment_type",
        "description": "Campus card (one-card) payment acceptance at any Quickcharge-enabled location",
        "dependencies": ["Quickcharge Server", "Campus Card System"],
        "triggers": ["campus card", "one card", "one-card", "id card", "student card", "staff card"],
    },
    # -- Infrastructure --
    {
        "name": "Quickcharge Server",
        "sku": "QC-SRV-300",
        "category": "infrastructure",
        "subcategory": "server",
        "description": "Central transaction processing server -- on-premises or cloud-hosted",
        "dependencies": ["Network infrastructure", "Database"],
        "triggers": [],  # always included when any QC product is matched
    },
    {
        "name": "Transact Cloud POS",
        "sku": "TC-CPOS-600",
        "category": "infrastructure",
        "subcategory": "cloud",
        "description": "Cloud-based POS platform with centralized reporting and menu management",
        "dependencies": ["Network infrastructure", "Transact cloud account"],
        "triggers": ["cloud pos", "cloud-based", "centralized reporting", "menu management"],
    },
    # -- Integrations --
    {
        "name": "Payroll/ERP Connector",
        "sku": "QC-INT-500",
        "category": "integration",
        "subcategory": "erp",
        "description": "Bidirectional integration with payroll/ERP systems (ADP, Workday, PeopleSoft, etc.)",
        "dependencies": ["Quickcharge Server"],
        "triggers": ["payroll", "erp", "adp", "workday", "peoplesoft", "hr system", "payroll system"],
    },
    {
        "name": "Identity Provider Connector",
        "sku": "QC-INT-510",
        "category": "integration",
        "subcategory": "identity",
        "description": "LDAP/SAML/OAuth2 integration for single sign-on and identity sync",
        "dependencies": ["Quickcharge Server"],
        "triggers": ["ldap", "saml", "sso", "single sign-on", "active directory", "identity"],
    },
    {
        "name": "NFC Reader (Mobile Credential)",
        "sku": "TC-NFC-700",
        "category": "hardware",
        "subcategory": "access",
        "description": "NFC reader compatible with Transact Mobile Credential -- Apple, Google, Samsung Wallet",
        "dependencies": ["Apple/Google VAS configuration"],
        "triggers": ["nfc", "contactless", "tap", "apple wallet", "google wallet", "samsung wallet", "mobile credential"],
    },
]


def match_products(parsed_notes: dict[str, Any]) -> list[dict[str, Any]]:
    """Match parsed discovery note entities against the product catalog.

    Returns matched products with the reason they matched.
    """
    matches: list[dict[str, Any]] = []
    matched_skus: set[str] = set()
    text_blob = _build_text_blob(parsed_notes)

    for product in PRODUCTS:
        for trigger in product["triggers"]:
            if trigger.lower() in text_blob:
                if product["sku"] not in matched_skus:
                    matched_skus.add(product["sku"])
                    matches.append({
                        "name": product["name"],
                        "sku": product["sku"],
                        "category": product["category"],
                        "description": product["description"],
                        "match_reason": f"Matched trigger: '{trigger}'",
                        "dependencies": product["dependencies"],
                    })
                break

    # always include Quickcharge Server if any QC product matched
    qc_server_needed = any(
        "Quickcharge Server" in m.get("dependencies", []) for m in matches
    )
    if qc_server_needed and "QC-SRV-300" not in matched_skus:
        srv = next(p for p in PRODUCTS if p["sku"] == "QC-SRV-300")
        matched_skus.add(srv["sku"])
        matches.append({
            "name": srv["name"],
            "sku": srv["sku"],
            "category": srv["category"],
            "description": srv["description"],
            "match_reason": "Required dependency for matched products",
            "dependencies": srv["dependencies"],
        })

    return matches


def build_mermaid_graph(
    parsed_notes: dict[str, Any],
    product_matches: list[dict[str, Any]],
) -> str:
    """Generate a Mermaid.js flowchart from parsed notes and matched products."""
    lines = ["graph TD"]
    locations = parsed_notes.get("locations", [])
    integrations = parsed_notes.get("integrations", [])
    payment_methods = parsed_notes.get("payment_methods", [])

    # payment entry points
    has_mobile = any(m["category"] == "software" and "mobile" in m.get("sku", "").lower() for m in product_matches)
    has_kiosk = any("kiosk" in m["name"].lower() for m in product_matches)
    has_pos = any("pos terminal" in m["name"].lower() for m in product_matches)

    # locations -> POS
    for i, loc in enumerate(locations):
        loc_id = f"LOC{i}"
        loc_label = loc.get("name", f"Location {i+1}")
        count = loc.get("register_count", 1)
        lines.append(f'    {loc_id}["{loc_label}"]')
        if has_pos:
            lines.append(f'    {loc_id} --> POS["Quickcharge POS<br/>{count}x terminals"]')

    if has_kiosk:
        lines.append('    KIOSK["Self-Service Kiosk"] --> QCS')
        if has_pos:
            lines.append('    POS --> QCS')
    elif has_pos:
        lines.append('    POS --> QCS')

    lines.append('    QCS["Quickcharge Server"]')

    if has_mobile:
        lines.append('    MOB["Mobile Ordering"] --> QCS')

    # payment method branches
    for pm in payment_methods:
        method = pm.get("method", "")
        if "payroll" in method.lower():
            lines.append('    QCS --> PAYROLL["Payroll/ERP"]')
        elif "meal" in method.lower() or "plan" in method.lower():
            lines.append('    QCS --> MEALPLAN["Meal Plan<br/>Management"]')
        elif "campus" in method.lower() or "card" in method.lower():
            lines.append('    QCS --> CAMPUS["Campus Card<br/>System"]')

    # integrations
    for integ in integrations:
        sys_name = integ.get("system", "External System")
        sys_id = sys_name.upper().replace(" ", "_").replace("/", "_")
        lines.append(f'    QCS <--> {sys_id}["{sys_name}"]')

    # styling
    lines.append("")
    lines.append("    classDef hw fill:#4a90d9,stroke:#2c5282,color:#fff")
    lines.append("    classDef sw fill:#48bb78,stroke:#276749,color:#fff")
    lines.append("    classDef infra fill:#ed8936,stroke:#c05621,color:#fff")
    if has_pos:
        lines.append("    class POS hw")
    if has_kiosk:
        lines.append("    class KIOSK hw")
    if has_mobile:
        lines.append("    class MOB sw")
    lines.append("    class QCS infra")

    return "\n".join(lines)


def get_integration_points(product_matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract API integration points from matched products."""
    points = []
    for m in product_matches:
        if m["category"] == "integration":
            points.append({
                "endpoint": m["name"],
                "protocol": "REST",
                "auth_method": "API Key / OAuth2",
                "direction": "bidirectional",
                "purpose": m["description"],
            })
    return points


def _build_text_blob(parsed_notes: dict[str, Any]) -> str:
    """Combine all text fields from parsed notes into a single lowercase string."""
    parts: list[str] = []
    for loc in parsed_notes.get("locations", []):
        parts.append(loc.get("name", ""))
        parts.append(loc.get("source_quote", ""))
    for hw in parsed_notes.get("hardware", []):
        parts.append(hw.get("item", ""))
        parts.append(hw.get("context", ""))
        parts.append(hw.get("source_quote", ""))
    for pm in parsed_notes.get("payment_methods", []):
        parts.append(pm.get("method", ""))
        parts.append(pm.get("source_quote", ""))
    for integ in parsed_notes.get("integrations", []):
        parts.append(integ.get("system", ""))
        parts.append(integ.get("source_quote", ""))
    for pp in parsed_notes.get("pain_points", []):
        parts.append(pp.get("text", ""))
    return " ".join(parts).lower()
