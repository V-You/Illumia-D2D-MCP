"""Entity extraction from raw discovery notes.

Regex + keyword extraction + structural heuristics. The LLM handles
ambiguity; this module extracts concrete entities.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


# -- location patterns ---------------------------------------------------------

_LOCATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?:the\s+)?(?P<name>[A-Z][\w\s]*?(?:cafeteria|dining|cafe|restaurant|"
        r"gift\s*shop|retail|lobby|food\s*court|kitchen|snack\s*bar|"
        r"coffee\s*shop|bistro|grill|deli))"
        r"(?:\s*(?::|,|has|with)\s*(?P<count>\d+)\s*(?:register|terminal|pos|checkout)s?)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<name>(?:main|satellite|floor\s*\d+|building\s*\w+)\s+"
        r"(?:cafeteria|cafe|dining|retail|shop))"
        r"(?:\s*(?::|,|has|with)\s*(?P<count>\d+)\s*(?:register|terminal|pos|checkout)s?)?",
        re.IGNORECASE,
    ),
]

_REGISTER_PATTERN = re.compile(
    r"(\d+)\s*(?:register|terminal|pos|checkout|counter)s?",
    re.IGNORECASE,
)

_LOCATION_TYPE_MAP = {
    "cafeteria": "dining", "dining": "dining", "cafe": "dining",
    "restaurant": "dining", "food court": "dining", "bistro": "dining",
    "grill": "dining", "deli": "dining", "coffee shop": "dining",
    "snack bar": "dining", "kitchen": "dining",
    "gift shop": "retail", "retail": "retail", "shop": "retail",
    "lobby": "common_area",
}

# -- hardware patterns ---------------------------------------------------------

_HARDWARE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?:physical\s+)?(?:prox(?:imity)?\s*cards?|badge\s*readers?)", re.IGNORECASE), "access"),
    (re.compile(r"nfc\s*readers?|contactless\s*readers?", re.IGNORECASE), "access"),
    (re.compile(r"card\s*readers?|swipe\s*readers?", re.IGNORECASE), "payment"),
    (re.compile(r"kiosks?|self[- ]service", re.IGNORECASE), "self_service"),
    (re.compile(r"(?:pos|point[- ]of[- ]sale)\s*(?:system|terminal)?", re.IGNORECASE), "point_of_sale"),
    (re.compile(r"registers?", re.IGNORECASE), "point_of_sale"),
]

# -- payment method patterns ---------------------------------------------------

_PAYMENT_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"payroll\s*deduct(?:ion)?", re.IGNORECASE), "payroll_deduct", "desired"),
    (re.compile(r"meal\s*plan", re.IGNORECASE), "meal_plan", "desired"),
    (re.compile(r"declining\s*balance|flex\s*dollars?", re.IGNORECASE), "declining_balance", "desired"),
    (re.compile(r"account\s*funding|add\s*funds", re.IGNORECASE), "account_funding", "desired"),
    (re.compile(r"mobile\s*(?:ordering|order|payment)", re.IGNORECASE), "mobile_ordering", "desired"),
    (re.compile(r"campus\s*card|one[- ]card|student\s*(?:id|card)|staff\s*(?:id|card)", re.IGNORECASE), "campus_card", "current"),
    (re.compile(r"credit|debit|visa|mastercard", re.IGNORECASE), "credit_debit", "current"),
    (re.compile(r"apple\s*(?:wallet|pay)", re.IGNORECASE), "mobile_wallet", "desired"),
    (re.compile(r"google\s*(?:wallet|pay)", re.IGNORECASE), "mobile_wallet", "desired"),
    (re.compile(r"cash(?:less)?", re.IGNORECASE), "cash", "current"),
]

# -- integration patterns ------------------------------------------------------

_INTEGRATION_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"(?:adp|workday|peoplesoft|kronos|ultipro)\b", re.IGNORECASE), "erp", ""),
    (re.compile(r"payroll\s*(?:system|integration|sync)", re.IGNORECASE), "erp", "payroll"),
    (re.compile(r"erp|enterprise\s*resource", re.IGNORECASE), "erp", "erp"),
    (re.compile(r"ldap|active\s*directory|saml|sso|single\s*sign", re.IGNORECASE), "identity", "identity_provider"),
    (re.compile(r"hr\s*system|human\s*resources?", re.IGNORECASE), "erp", "hr"),
]

# -- pain point patterns -------------------------------------------------------

_PAIN_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?:reconciliation|reconcile)\s*(?:is\s+)?(?:a\s+)?(?:nightmare|difficult|hard|manual|painful)", re.IGNORECASE), "fragmented_reporting"),
    (re.compile(r"separate\s+(?:reporting|pos|system|vendor)", re.IGNORECASE), "fragmented_reporting"),
    (re.compile(r"different\s+(?:reporting|pos|system|vendor)", re.IGNORECASE), "fragmented_reporting"),
    (re.compile(r"(?:manual|manually)\s+(?:billing|billed|reconcil|process|entry|data)", re.IGNORECASE), "manual_process"),
    (re.compile(r"excel\s*(?:spreadsheet|billing|tracking)", re.IGNORECASE), "manual_process"),
    (re.compile(r"(?:can'?t|cannot|unable)\s+(?:see|view|track)\s+(?:real[- ]time|live)", re.IGNORECASE), "lack_of_visibility"),
    (re.compile(r"fragmented|siloed|silo", re.IGNORECASE), "fragmented_reporting"),
]

# -- staff count ---------------------------------------------------------------

_STAFF_PATTERN = re.compile(
    r"(\d[\d,]*)\s*(?:staff|employee|worker|personnel|people)(?:\s*/\s*day)?",
    re.IGNORECASE,
)


def parse_notes(text: str) -> dict[str, Any]:
    """Parse raw discovery notes into structured entities."""
    locations = _extract_locations(text)
    hardware = _extract_hardware(text)
    payment_methods = _extract_payment_methods(text)
    integrations = _extract_integrations(text)
    pain_points = _extract_pain_points(text)
    staff_count = _extract_staff_count(text)

    return {
        "locations": locations,
        "hardware": hardware,
        "payment_methods": payment_methods,
        "integrations": integrations,
        "pain_points": pain_points,
        "staff_count": staff_count,
    }


def read_notes_file(file_path: str) -> str:
    """Read notes from a local file. Returns file contents."""
    p = Path(file_path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not p.suffix.lower() in (".md", ".txt", ".text", ".notes"):
        raise ValueError(f"Unsupported file type: {p.suffix} (expected .md or .txt)")
    return p.read_text(encoding="utf-8")


def _extract_locations(text: str) -> list[dict[str, Any]]:
    locations: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    for pattern in _LOCATION_PATTERNS:
        for m in pattern.finditer(text):
            name = m.group("name").strip()
            name_lower = name.lower()
            if name_lower in seen_names:
                continue
            seen_names.add(name_lower)

            count = int(m.group("count")) if m.group("count") else None
            loc_type = "other"
            for keyword, ltype in _LOCATION_TYPE_MAP.items():
                if keyword in name_lower:
                    loc_type = ltype
                    break

            # look for register count near location if not in the match
            if count is None:
                context = text[max(0, m.start() - 20):m.end() + 80]
                reg_m = _REGISTER_PATTERN.search(context)
                if reg_m:
                    count = int(reg_m.group(1))

            locations.append({
                "name": name,
                "type": loc_type,
                "register_count": count,
                "source_quote": _get_source_quote(text, m.start(), m.end()),
            })

    # fallback: look for "Floor X cafe" etc. in bullet points
    for line in text.split("\n"):
        line_stripped = line.strip().lstrip("-*• ")
        if not line_stripped:
            continue
        for keyword, ltype in _LOCATION_TYPE_MAP.items():
            if keyword in line_stripped.lower() and line_stripped.lower() not in seen_names:
                name = line_stripped.split(":")[0].strip() if ":" in line_stripped else line_stripped[:60]
                if name.lower() not in seen_names:
                    seen_names.add(name.lower())
                    reg_m = _REGISTER_PATTERN.search(line_stripped)
                    count = int(reg_m.group(1)) if reg_m else None
                    locations.append({
                        "name": name,
                        "type": ltype,
                        "register_count": count,
                        "source_quote": line_stripped[:120],
                    })
                break

    return locations


def _extract_hardware(text: str) -> list[dict[str, Any]]:
    hardware: list[dict[str, Any]] = []
    seen: set[str] = set()

    for pattern, context_type in _HARDWARE_PATTERNS:
        for m in pattern.finditer(text):
            item = m.group(0).strip()
            item_lower = item.lower()
            if item_lower in seen:
                continue
            seen.add(item_lower)
            hardware.append({
                "item": item,
                "context": context_type,
                "source_quote": _get_source_quote(text, m.start(), m.end()),
            })

    return hardware


def _extract_payment_methods(text: str) -> list[dict[str, Any]]:
    methods: list[dict[str, Any]] = []
    seen: set[str] = set()

    for pattern, method_name, status in _PAYMENT_PATTERNS:
        for m in pattern.finditer(text):
            if method_name in seen:
                continue
            seen.add(method_name)
            # check if "want" / "need" / "looking for" near match -> desired
            ctx = text[max(0, m.start() - 60):m.end() + 20].lower()
            actual_status = status
            if any(w in ctx for w in ["want", "need", "looking", "interested", "asked about"]):
                actual_status = "desired"
            elif any(w in ctx for w in ["currently", "existing", "already", "use", "have"]):
                actual_status = "current"

            methods.append({
                "method": method_name,
                "status": actual_status,
                "source_quote": _get_source_quote(text, m.start(), m.end()),
            })

    return methods


def _extract_integrations(text: str) -> list[dict[str, Any]]:
    integrations: list[dict[str, Any]] = []
    seen: set[str] = set()

    for pattern, integ_type, system_hint in _INTEGRATION_PATTERNS:
        for m in pattern.finditer(text):
            matched_text = m.group(0).strip()
            # use matched text as system name if no hint
            system = system_hint if system_hint else matched_text
            key = f"{integ_type}:{system.lower()}"
            if key in seen:
                continue
            seen.add(key)
            integrations.append({
                "system": system if system else matched_text,
                "type": integ_type,
                "source_quote": _get_source_quote(text, m.start(), m.end()),
            })

    return integrations


def _extract_pain_points(text: str) -> list[dict[str, Any]]:
    pain_points: list[dict[str, Any]] = []

    for pattern, category in _PAIN_PATTERNS:
        for m in pattern.finditer(text):
            pain_points.append({
                "text": _get_source_quote(text, m.start(), m.end()),
                "category": category,
            })

    return pain_points


def _extract_staff_count(text: str) -> int | None:
    m = _STAFF_PATTERN.search(text)
    if m:
        return int(m.group(1).replace(",", ""))
    return None


def _get_source_quote(text: str, start: int, end: int) -> str:
    """Extract a reasonable source quote around a match."""
    # expand to sentence boundaries
    line_start = text.rfind("\n", 0, start)
    line_start = line_start + 1 if line_start >= 0 else 0
    line_end = text.find("\n", end)
    line_end = line_end if line_end >= 0 else len(text)
    quote = text[line_start:line_end].strip().lstrip("-*• ")
    return quote[:200]
