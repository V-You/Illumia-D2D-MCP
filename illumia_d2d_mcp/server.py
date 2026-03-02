"""Illumia D2D MCP server.

FastMCP server with 5 tools:
- ingest_discovery_notes: parse raw walkthrough notes into structured entities
- map_to_quickcharge_stack: match needs to Quickcharge products + workflow map
- generate_system_bom: produce hardware/software/integration BOM
- detect_cross_sell_leads: find cross-sell opportunities for other Illumia products
- query_illumia_docs: query bundled product documentation
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.apps import AppConfig
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from illumia_d2d_mcp.cross_sell import detect_leads
from illumia_d2d_mcp.demo_mode import DemoMode, get_demo_mode, load_fixture
from illumia_d2d_mcp.errors import make_error_envelope
from illumia_d2d_mcp.note_parser import parse_notes, read_notes_file
from illumia_d2d_mcp.product_catalog import (
    build_mermaid_graph,
    get_integration_points,
    match_products,
)
from illumia_d2d_mcp.widgets import (
    render_cross_sell_dashboard,
    render_docs_panel,
    render_parsed_notes,
    render_system_bom,
    render_workflow_map,
)

log = logging.getLogger("illumia_d2d_mcp.server")

DOCS_PATH = Path(__file__).parent / "docs_context.md"

mcp = FastMCP(
    "Illumia D2D",
    instructions=(
        "Discovery-to-Diagram: translate campus walkthrough notes into "
        "Quickcharge architectures, hardware BOMs, and cross-sell leads."
    ),
)

_last_results: dict[str, dict[str, Any]] = {}


# -- tools --------------------------------------------------------------------


@mcp.tool(
    app=AppConfig(resource_uri="ui://illumia-d2d/parsed-notes.html"),
)
def ingest_discovery_notes(
    notes: str = "",
    file_path: str = "",
) -> ToolResult:
    """Parse raw discovery notes from a campus walkthrough into structured entities.

    Extracts locations, hardware, payment methods, integrations, and pain
    points from unstructured text. Provide notes directly or point to a file.

    Args:
        notes: raw text, bullet points, or transcript from a discovery call.
        file_path: path to a local .md or .txt file containing the notes.
    """
    mode = get_demo_mode()

    if mode == DemoMode.MOCK:
        result = load_fixture("ingest_discovery_notes")
        _last_results["parsed_notes"] = result
        return _notes_result(result)

    # resolve input
    if file_path:
        try:
            raw_text = read_notes_file(file_path)
        except FileNotFoundError:
            return ToolResult(
                content=[TextContent(type="text", text="")],
                structured_content=make_error_envelope(
                    code="file_not_found",
                    message=f"File not found: {file_path}",
                    suggested_action="Check the file path and try again.",
                ),
            )
        except ValueError as exc:
            return ToolResult(
                content=[TextContent(type="text", text="")],
                structured_content=make_error_envelope(
                    code="invalid_input",
                    message=str(exc),
                    suggested_action="Provide a .md or .txt file.",
                ),
            )
    elif notes:
        raw_text = notes
    else:
        return ToolResult(
            content=[TextContent(type="text", text="")],
            structured_content=make_error_envelope(
                code="invalid_input",
                message="No input provided. Supply either 'notes' text or a 'file_path'.",
                suggested_action="Paste your discovery notes or provide a file path.",
            ),
        )

    parsed = parse_notes(raw_text)

    total_entities = (
        len(parsed["locations"])
        + len(parsed["hardware"])
        + len(parsed["payment_methods"])
        + len(parsed["integrations"])
        + len(parsed["pain_points"])
    )

    if total_entities == 0:
        return ToolResult(
            content=[TextContent(type="text", text="")],
            structured_content=make_error_envelope(
                code="parse_error",
                message="No extractable entities found in input text.",
                suggested_action="Provide more detailed notes with locations, hardware, or payment methods.",
            ),
        )

    result = {"parsed_notes": parsed, "_source": "local"}
    _last_results["parsed_notes"] = result

    return _notes_result(result)


def _notes_result(result: dict[str, Any]) -> ToolResult:
    parsed = result.get("parsed_notes", result)
    loc_count = len(parsed.get("locations", []))
    hw_count = len(parsed.get("hardware", []))
    pm_count = len(parsed.get("payment_methods", []))
    int_count = len(parsed.get("integrations", []))
    pp_count = len(parsed.get("pain_points", []))

    text = (
        f"Extracted {loc_count} locations, {hw_count} hardware items, "
        f"{pm_count} payment methods, {int_count} integrations, "
        f"and {pp_count} pain points.\n\n"
        "The widget above shows all entities grouped by category. "
        "Do NOT repeat the entity list. Instead summarize briefly and suggest:\n"
        "- Next step: run map_to_quickcharge_stack with these parsed notes\n"
        "- Or: run detect_cross_sell_leads to find ecosystem opportunities"
    )

    return ToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=result,
        meta={"ui": {"resourceUri": "ui://illumia-d2d/parsed-notes.html"}},
    )


@mcp.tool(
    app=AppConfig(resource_uri="ui://illumia-d2d/workflow-map.html"),
)
def map_to_quickcharge_stack(
    parsed_notes: dict[str, Any],
) -> ToolResult:
    """Map parsed discovery notes to the Quickcharge product stack.

    Cross-references extracted needs against the bundled product catalog
    and generates a Mermaid.js workflow diagram of the proposed architecture.

    Args:
        parsed_notes: structured JSON from ingest_discovery_notes (with
            locations, hardware, payment_methods, integrations, pain_points).
    """
    mode = get_demo_mode()

    if mode == DemoMode.MOCK:
        result = load_fixture("map_to_quickcharge_stack")
        _last_results["workflow_map"] = result
        return _workflow_result(result)

    products = match_products(parsed_notes)

    if not products:
        return ToolResult(
            content=[TextContent(type="text", text="")],
            structured_content=make_error_envelope(
                code="no_matches",
                message="No matching Quickcharge products found for the provided notes.",
                suggested_action="Ensure notes mention specific needs (POS, kiosks, mobile ordering, payroll deduct, etc.).",
            ),
        )

    mermaid = build_mermaid_graph(parsed_notes, products)
    integrations = get_integration_points(products)

    result = {
        "product_matches": products,
        "workflow_graph": mermaid,
        "integration_points": integrations,
        "_source": "local",
    }
    _last_results["workflow_map"] = result

    return _workflow_result(result)


def _workflow_result(result: dict[str, Any]) -> ToolResult:
    matches = result.get("product_matches", [])
    integrations = result.get("integration_points", [])

    text = (
        f"Matched {len(matches)} products and {len(integrations)} integration points.\n\n"
        "The widget above shows the Mermaid.js architecture diagram and "
        "product match table. Do NOT repeat either. Instead:\n"
        "- Summarize the proposed architecture in 2-3 sentences\n"
        "- Suggest running generate_system_bom for a detailed BOM"
    )

    return ToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=result,
        meta={"ui": {"resourceUri": "ui://illumia-d2d/workflow-map.html"}},
    )


@mcp.tool(
    app=AppConfig(resource_uri="ui://illumia-d2d/system-bom.html"),
)
def generate_system_bom(
    parsed_notes: dict[str, Any],
    product_matches: list[dict[str, Any]],
) -> ToolResult:
    """Generate a Bill of Materials from parsed notes and matched products.

    Produces hardware, software, and API integration items with quantities
    derived from location register counts and staff estimates.

    Args:
        parsed_notes: structured JSON from ingest_discovery_notes.
        product_matches: product match list from map_to_quickcharge_stack.
    """
    mode = get_demo_mode()

    if mode == DemoMode.MOCK:
        result = load_fixture("generate_system_bom")
        _last_results["system_bom"] = result
        return _bom_result(result)

    bom_items: list[dict[str, Any]] = []
    locations = parsed_notes.get("locations", [])

    for match in product_matches:
        quantity = 1
        context = ""

        if match["category"] == "hardware" and "pos" in match["name"].lower():
            # sum register counts across locations
            total_registers = sum(loc.get("register_count", 1) or 1 for loc in locations)
            quantity = total_registers
            context = ", ".join(
                f"{loc.get('name', 'Location')} -- {loc.get('register_count', 1) or 1} registers"
                for loc in locations
            ) if locations else "1 location"
        elif match["category"] == "hardware" and "kiosk" in match["name"].lower():
            # count kiosk mentions
            kiosk_mentions = sum(
                1 for hw in parsed_notes.get("hardware", [])
                if "kiosk" in hw.get("item", "").lower()
            )
            quantity = max(kiosk_mentions, 1)
            context = f"{quantity} kiosk location(s)"
        else:
            context = match.get("match_reason", "")

        bom_items.append({
            "item": match["name"],
            "category": match["category"],
            "quantity": quantity,
            "unit_context": context,
            "dependencies": match.get("dependencies", []),
        })

    api_integrations = get_integration_points(product_matches)

    hw_count = sum(1 for b in bom_items if b["category"] == "hardware")
    sw_count = sum(1 for b in bom_items if b["category"] == "software")
    infra_count = sum(1 for b in bom_items if b["category"] == "infrastructure")
    int_count = len(api_integrations)

    total = hw_count + sw_count + infra_count + int_count
    complexity = "low" if total <= 4 else ("medium" if total <= 8 else "high")

    result = {
        "bom_items": bom_items,
        "api_integrations": api_integrations,
        "summary": {
            "total_hardware_items": hw_count,
            "total_software_items": sw_count + infra_count,
            "total_integrations": int_count,
            "estimated_complexity": complexity,
        },
        "_source": "local",
    }
    _last_results["system_bom"] = result

    return _bom_result(result)


def _bom_result(result: dict[str, Any]) -> ToolResult:
    summary = result.get("summary", {})
    text = (
        f"BOM: {summary.get('total_hardware_items', 0)} hardware, "
        f"{summary.get('total_software_items', 0)} software, "
        f"{summary.get('total_integrations', 0)} integrations. "
        f"Complexity: {summary.get('estimated_complexity', 'unknown')}.\n\n"
        "The widget above shows the full BOM table. Do NOT repeat it. Instead:\n"
        "- Highlight the most critical dependencies\n"
        "- Suggest running detect_cross_sell_leads for ecosystem opportunities"
    )

    return ToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=result,
        meta={"ui": {"resourceUri": "ui://illumia-d2d/system-bom.html"}},
    )


@mcp.tool(
    app=AppConfig(resource_uri="ui://illumia-d2d/cross-sell-dashboard.html"),
)
def detect_cross_sell_leads(
    parsed_notes: dict[str, Any],
) -> ToolResult:
    """Scan discovery notes for cross-sell opportunities across the Illumia ecosystem.

    Detects triggers for Campus ID (Mobile Credential), Campus Commerce
    (Transact Insights), and Integrated Payments (Sponsor Payments).

    Args:
        parsed_notes: structured JSON from ingest_discovery_notes.
    """
    mode = get_demo_mode()

    if mode == DemoMode.MOCK:
        result = load_fixture("detect_cross_sell_leads")
        _last_results["cross_sell"] = result
        return _cross_sell_result(result)

    leads = detect_leads(parsed_notes)

    result = {"leads": leads, "_source": "local"}
    _last_results["cross_sell"] = result

    return _cross_sell_result(result)


def _cross_sell_result(result: dict[str, Any]) -> ToolResult:
    leads = result.get("leads", [])
    product_lines = set(l.get("product_line") for l in leads)

    if not leads:
        text = (
            "No cross-sell triggers detected in the discovery notes.\n"
            "Try providing more detailed notes that mention physical cards, "
            "separate reporting systems, or third-party billing."
        )
    else:
        text = (
            f"Found {len(leads)} cross-sell leads across {len(product_lines)} "
            f"product lines: {', '.join(product_lines)}.\n\n"
            "The widget above shows lead cards with trigger quotes, gap "
            "analysis, and recommended actions. Do NOT repeat them. Instead:\n"
            "- Summarize the business impact in 2-3 sentences\n"
            "- Emphasize the ecosystem revenue multiplier angle"
        )

    return ToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=result,
        meta={"ui": {"resourceUri": "ui://illumia-d2d/cross-sell-dashboard.html"}},
    )


@mcp.tool(
    app=AppConfig(resource_uri="ui://illumia-d2d/docs-panel.html"),
)
def query_illumia_docs(question: str) -> ToolResult:
    """Query bundled Illumia/Transact/CBORD product documentation.

    Returns documentation context for the LLM to extract a concise answer.
    Covers Quickcharge, Campus ID, Campus Commerce, and Integrated Payments.

    Args:
        question: natural-language question about Illumia/Transact products.
    """
    if not DOCS_PATH.exists():
        return ToolResult(
            content=[TextContent(type="text", text="")],
            structured_content=make_error_envelope(
                code="missing_docs",
                message="docs_context.md not found.",
                suggested_action="Ensure docs_context.md exists in the illumia_d2d_mcp package.",
            ),
        )

    content = DOCS_PATH.read_text(encoding="utf-8")
    result = {
        "question": question,
        "documentation": content,
        "_source": "local",
    }
    _last_results["docs"] = result

    text = (
        "Documentation loaded. Answer the user's question using the "
        "documentation context provided in structured_content. "
        "Keep the answer concise (3-5 sentences max) and cite the "
        "relevant product by name."
    )

    return ToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=result,
        meta={"ui": {"resourceUri": "ui://illumia-d2d/docs-panel.html"}},
    )


# -- ui:// resources -----------------------------------------------------------


@mcp.resource("ui://illumia-d2d/parsed-notes.html")
def parsed_notes_widget() -> str:
    """Interactive parsed notes widget."""
    data = _last_results.get("parsed_notes", {"parsed_notes": {}, "_source": "local"})
    return render_parsed_notes(data)


@mcp.resource("ui://illumia-d2d/workflow-map.html")
def workflow_map_widget() -> str:
    """Interactive workflow map widget with Mermaid.js diagram."""
    data = _last_results.get("workflow_map", {
        "product_matches": [], "workflow_graph": "graph TD\n    A[No data yet]",
        "integration_points": [], "_source": "local",
    })
    return render_workflow_map(data)


@mcp.resource("ui://illumia-d2d/system-bom.html")
def system_bom_widget() -> str:
    """System BOM table widget."""
    data = _last_results.get("system_bom", {
        "bom_items": [], "api_integrations": [], "summary": {}, "_source": "local",
    })
    return render_system_bom(data)


@mcp.resource("ui://illumia-d2d/cross-sell-dashboard.html")
def cross_sell_widget() -> str:
    """Cross-sell leads dashboard widget."""
    data = _last_results.get("cross_sell", {"leads": [], "_source": "local"})
    return render_cross_sell_dashboard(data)


@mcp.resource("ui://illumia-d2d/docs-panel.html")
def docs_panel_widget() -> str:
    """Documentation panel widget."""
    data = _last_results.get("docs", {
        "question": "", "documentation": "No query yet.", "_source": "local",
    })
    return render_docs_panel(data)


# -- entry point ---------------------------------------------------------------


def main() -> None:
    """Start the MCP server."""
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    log.info("starting Illumia D2D MCP server")
    mcp.run(show_banner=False)
