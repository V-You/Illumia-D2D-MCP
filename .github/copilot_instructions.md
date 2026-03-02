# Illumia D2D MCP Developer Instructions

You are an expert Python engineer building a local Model Context Protocol (MCP) server for the Illumia "Discovery-to-Diagram" (D2D) tool -- an SE Co-pilot that translates unstructured campus walkthrough notes into Quickcharge architectures, hardware BOMs, and cross-sell leads.

## Architecture Rules
1. **Framework:** Strictly use the `fastmcp` library (`from fastmcp import FastMCP`). Do NOT use the raw `mcp.server` low-level APIs.
2. **Transport:** The server is intended to be run locally as a child process by an IDE. Always use `stdio` transport. Never configure HTTP/SSE or open network ports (except the ephemeral localhost port for MCP Apps widget serving).
3. **Typing & Docstrings:** FastMCP relies heavily on Python type hints and docstrings to automatically generate JSON schemas for the LLM. You MUST provide detailed docstrings and strict type hints for every function decorated with `@mcp.tool` or `@mcp.resource`.
4. **Distribution:** Installable Python package via `pyproject.toml` + `uv`. Run with `uv run python -m illumia_d2d_mcp` locally or install from GitHub with `uvx --from git+https://github.com/V-You/Illumia-D2D-MCP illumia-d2d-mcp`. No Docker, no manual virtualenv.
5. **Error handling:** Domain errors (empty input, unreadable files, no matches) must be caught and returned as structured JSON error envelopes -- never let Python exceptions bubble up to FastMCP's protocol layer. The LLM reads error strings and guides the user.

## Capabilities to Implement
Whenever I ask you to add a feature, consider if it should be a:
- **Tool (`@mcp.tool`):** For actions that parse, generate, or transform data (e.g., parsing discovery notes, generating a BOM, detecting cross-sell leads).
- **Resource (`@mcp.resource`):** For read-only data (e.g., reading a local notes file, serving `ui://` widget HTML for MCP Apps).

If a tool accepts a file path, use `pathlib` to read the file. Assume the server is running in the root of the user's workspace.

## Project Structure
- `illumia_d2d_mcp/` -- Installable Python package
  - `server.py` -- MCP server (5 tools + 5 ui:// resources)
  - `note_parser.py` -- Entity extraction from raw discovery notes
  - `product_catalog.py` -- Bundled Quickcharge/Transact product data
  - `cross_sell.py` -- Cross-sell trigger map and lead detection
  - `widgets.py` -- HTML widget renderers (MCP Apps)
  - `demo_mode.py` -- Live/mock/auto-fallback decorator
  - `errors.py` -- Error envelope
  - `docs_context.md` -- Bundled Quickcharge/Transact/CBORD product documentation
  - `fixtures/` -- Per-tool demo fixtures (Hospital Complex scenario)
  - `__init__.py` / `__main__.py` -- Package entry points
- `src/` -- Widget source (React + TypeScript)
  - `parsed-notes/` -- Entity cards
  - `workflow-map/` -- Mermaid.js flowchart
  - `system-bom/` -- BOM table
  - `cross-sell-dashboard/` -- Cross-sell lead cards
  - `docs-panel/` -- Documentation panel
- `assets/` -- Built widgets (tracked for distribution)
- `pyproject.toml` -- Build system (hatchling), dependencies & entry points
- `.github/skills/illumia/SKILL.md` -- SE persona skill
- `.github/skills/illumia-xsell/SKILL.md` -- Cross-sell persona skill

## Code, Style
- KISS
- DRY
- Brief comments, if even
- Never use m-dash, use n-dash instead (surrounded by whitespace)
- No emojis
- Before changing any file, create a backup copy, extension .bak.YYYYMMDD, in bak/
- If code seems missing anywhere, look in bak/ for most recent version and cherry pick from there