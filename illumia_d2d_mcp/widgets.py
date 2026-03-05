"""HTML widget renderers for MCP Apps.

Each function returns a self-contained HTML string for rendering in the
VS Code chat panel via the ui:// resource protocol.

All widgets use JS-driven rendering: data is embedded as JSON and rendered
via a ``renderData()`` function, which is also called from ``applyToolResult``
when the ``tool-result`` message arrives — ensuring the widget always shows
data regardless of resource-fetch timing.
"""

from __future__ import annotations

import html
import json
from typing import Any


def _mcp_apps_js(widget_name: str, render_data_body: str) -> str:
    """MCP Apps handshake + tool-result JS boilerplate.

    ``render_data_body`` is the body of ``function renderData(data) { ... }``.
    It is called once on page load with embedded data, and again whenever
    ``tool-result`` delivers new structuredContent.
    """
    template = """
    const pendingReqs = new Map();
    let msgId = 1;

    function mcpRequest(method, params) {
      return new Promise((resolve, reject) => {
        const id = msgId++;
        pendingReqs.set(id, { resolve, reject });
        window.parent.postMessage({ jsonrpc: "2.0", id, method, params: params || {} }, "*");
      });
    }

    function mcpNotify(method, params) {
      window.parent.postMessage({ jsonrpc: "2.0", method, params: params || {} }, "*");
    }

    function applyHostContext(ctx) {
      if (ctx && ctx.styles && ctx.styles.variables) {
        for (const [k, v] of Object.entries(ctx.styles.variables)) {
          document.documentElement.style.setProperty(k, v);
        }
      }
      if (ctx && ctx.theme) {
        document.documentElement.style.colorScheme = ctx.theme;
      }
    }

    function esc(s) { const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }

    function renderData(data) {
      __RENDER_DATA_BODY__
    }

    window.addEventListener("message", (e) => {
      const data = e.data;
      if (!data || data.jsonrpc !== "2.0") return;

      if (data.id !== undefined && (data.result !== undefined || data.error)) {
        const p = pendingReqs.get(data.id);
        if (p) {
          pendingReqs.delete(data.id);
          if (data.error) p.reject(new Error(data.error.message));
          else p.resolve(data.result);
        }
        return;
      }

      if (data.method === "ui/notifications/host-context-changed") {
        applyHostContext(data.params);
      }

      if (data.method === "ui/notifications/tool-result" && data.params) {
        const sc = data.params.structuredContent;
        if (sc) {
          renderData(sc);
        }
      }
    });

    (async () => {
      try {
        const res = await mcpRequest("ui/initialize", {
          protocolVersion: "2026-01-26",
          appCapabilities: {},
          appInfo: { name: "__WIDGET_NAME__", version: "1.0.0" }
        });
        if (res && res.hostContext) {
          applyHostContext(res.hostContext);
        }
        mcpNotify("ui/notifications/initialized", {});
      } catch (err) {
        console.warn("MCP Apps init failed", err);
      }
    })();

    // render with embedded initial data
    renderData(window.__INITIAL_DATA__ || {});
    """
    return template.replace("__WIDGET_NAME__", widget_name).replace(
        "__RENDER_DATA_BODY__", render_data_body
    )


_BASE_STYLES = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: var(--vscode-font-family, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif);
      font-size: var(--vscode-font-size, 13px);
      color: var(--vscode-foreground, #ccc);
      background: var(--vscode-editor-background, #1e1e1e);
      padding: 12px;
    }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 11px;
      font-weight: 600;
    }
    .badge.live { background: #276749; color: #c6f6d5; }
    .badge.simulated { background: #744210; color: #fefcbf; }
    .header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
    .header h2 { font-size: 14px; font-weight: 600; }
    .stats { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
    .stat-card {
      background: var(--vscode-input-background, #2d2d2d);
      border: 1px solid var(--vscode-input-border, #3e3e3e);
      border-radius: 6px;
      padding: 8px 12px;
      min-width: 80px;
    }
    .stat-card .label { font-size: 11px; opacity: 0.7; }
    .stat-card .value { font-size: 18px; font-weight: 700; }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
    }
    th, td {
      text-align: left;
      padding: 6px 10px;
      border-bottom: 1px solid var(--vscode-input-border, #3e3e3e);
      font-size: 12px;
    }
    th {
      background: var(--vscode-input-background, #2d2d2d);
      font-weight: 600;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      opacity: 0.8;
    }
    .quote {
      font-style: italic;
      opacity: 0.7;
      font-size: 11px;
    }
    .category-hw { color: #63b3ed; }
    .category-sw { color: #68d391; }
    .category-infra { color: #ed8936; }
    .category-int { color: #d69e2e; }
    .card {
      background: var(--vscode-input-background, #2d2d2d);
      border: 1px solid var(--vscode-input-border, #3e3e3e);
      border-radius: 6px;
      padding: 12px;
      margin-bottom: 8px;
    }
    .card h3 { font-size: 13px; font-weight: 600; margin-bottom: 4px; }
    .card p { font-size: 12px; margin-top: 4px; }
    .tag {
      display: inline-block;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 600;
      margin-right: 4px;
    }
    .tag.dining { background: #2d3748; color: #a0aec0; }
    .tag.retail { background: #44337a; color: #d6bcfa; }
    .tag.current { background: #276749; color: #c6f6d5; }
    .tag.desired { background: #2a4365; color: #90cdf4; }
"""


def render_parsed_notes(data: dict[str, Any]) -> str:
    """Render ingest_discovery_notes results."""
    data_json = json.dumps(data, default=str)

    js = _mcp_apps_js("illumia-parsed-notes", """
      const parsed = data.parsed_notes || data;
      const locs = parsed.locations || [];
      const hw = parsed.hardware || [];
      const pms = parsed.payment_methods || [];
      const ints = parsed.integrations || [];
      const pps = parsed.pain_points || [];
      const staff = parsed.staff_count;
      const src = data._source || 'unknown';

      // badge
      const badge = document.getElementById('badge');
      badge.className = 'badge ' + (src === 'live' ? 'live' : 'simulated');
      badge.textContent = src === 'live' ? 'Live' : 'Simulated';

      // stats
      document.getElementById('stat-loc').textContent = locs.length;
      document.getElementById('stat-hw').textContent = hw.length;
      document.getElementById('stat-pm').textContent = pms.length;
      document.getElementById('stat-int').textContent = ints.length;
      document.getElementById('stat-pp').textContent = pps.length;
      const staffCard = document.getElementById('stat-staff-card');
      if (staff) { staffCard.style.display = ''; document.getElementById('stat-staff').textContent = staff; }
      else { staffCard.style.display = 'none'; }

      // locations
      let locHtml = '';
      if (locs.length) {
        locHtml = '<h3>Locations</h3>';
        for (const l of locs) {
          const cnt = l.register_count ? ' -- ' + l.register_count + ' registers' : '';
          locHtml += '<div class="card"><h3>' + esc(l.name) + ' <span class="tag ' + (l.type||'') + '">' + esc(l.type||'') + '</span>' + cnt + '</h3>' +
            (l.source_quote ? '<p class="quote">"' + esc(l.source_quote) + '"</p>' : '') + '</div>';
        }
      }
      document.getElementById('sec-loc').innerHTML = locHtml;

      // hardware
      let hwHtml = '';
      if (hw.length) {
        hwHtml = '<h3>Hardware</h3>';
        for (const h of hw) {
          hwHtml += '<div class="card"><h3>' + esc(h.item) + (h.count ? ' (x' + h.count + ')' : '') + '</h3>' +
            '<p>Context: ' + esc(h.context||'') + '</p>' +
            (h.source_quote ? '<p class="quote">"' + esc(h.source_quote) + '"</p>' : '') + '</div>';
        }
      }
      document.getElementById('sec-hw').innerHTML = hwHtml;

      // payment methods
      let pmHtml = '';
      if (pms.length) {
        pmHtml = '<h3>Payment Methods</h3><table><tr><th>Method</th><th>Status</th><th>Source</th></tr>';
        for (const p of pms) {
          pmHtml += '<tr><td>' + esc(p.method) + '</td><td><span class="tag ' + (p.status||'') + '">' + esc(p.status||'') + '</span></td>' +
            '<td class="quote">' + esc(p.source_quote||'') + '</td></tr>';
        }
        pmHtml += '</table>';
      }
      document.getElementById('sec-pm').innerHTML = pmHtml;

      // integrations
      let intHtml = '';
      if (ints.length) {
        intHtml = '<h3>Integrations</h3><table><tr><th>System</th><th>Type</th><th>Source</th></tr>';
        for (const i of ints) {
          intHtml += '<tr><td>' + esc(i.system) + '</td><td>' + esc(i.type||'') + '</td>' +
            '<td class="quote">' + esc(i.source_quote||'') + '</td></tr>';
        }
        intHtml += '</table>';
      }
      document.getElementById('sec-int').innerHTML = intHtml;

      // pain points
      let ppHtml = '';
      if (pps.length) {
        ppHtml = '<h3>Pain Points</h3>';
        for (const p of pps) {
          const txt = typeof p === 'string' ? p : (p.text || '');
          const cat = typeof p === 'string' ? '' : (p.category || '');
          ppHtml += '<div class="card" style="border-left:3px solid #e53e3e;"><p>"' + esc(txt) + '"</p>' +
            (cat ? '<p><span class="tag">' + esc(cat) + '</span></p>' : '') + '</div>';
        }
      }
      document.getElementById('sec-pp').innerHTML = ppHtml;
    """)

    return f"""<!DOCTYPE html>
<html><head><style>{_BASE_STYLES}</style></head>
<body>
  <div class="header">
    <h2>Discovery Notes -- Parsed Entities</h2>
    <span id="badge" class="badge simulated">Simulated</span>
  </div>
  <div class="stats">
    <div class="stat-card"><div class="label">Locations</div><div class="value" id="stat-loc">0</div></div>
    <div class="stat-card"><div class="label">Hardware</div><div class="value" id="stat-hw">0</div></div>
    <div class="stat-card"><div class="label">Payment Methods</div><div class="value" id="stat-pm">0</div></div>
    <div class="stat-card"><div class="label">Integrations</div><div class="value" id="stat-int">0</div></div>
    <div class="stat-card"><div class="label">Pain Points</div><div class="value" id="stat-pp">0</div></div>
    <div class="stat-card" id="stat-staff-card" style="display:none;"><div class="label">Staff/Day</div><div class="value" id="stat-staff">0</div></div>
  </div>
  <div id="sec-loc"></div>
  <div id="sec-hw"></div>
  <div id="sec-pm"></div>
  <div id="sec-int"></div>
  <div id="sec-pp"></div>
  <script>window.__INITIAL_DATA__ = {data_json};</script>
  <script>{js}</script>
</body></html>"""


def render_workflow_map(data: dict[str, Any]) -> str:
    """Render map_to_quickcharge_stack results with Mermaid.js flowchart."""
    data_json = json.dumps(data, default=str)

    js = _mcp_apps_js("illumia-workflow-map", """
      const src = data._source || 'unknown';
      const badge = document.getElementById('badge');
      badge.className = 'badge ' + (src === 'live' ? 'live' : 'simulated');
      badge.textContent = src === 'live' ? 'Live' : 'Simulated';

      const matches = data.product_matches || [];
      const intPoints = data.integration_points || [];
      const graph = data.workflow_graph || 'graph TD\\n    A[No data]';

      // mermaid
      const mc = document.getElementById('mermaid-container');
      mc.innerHTML = '<pre class="mermaid">' + esc(graph) + '</pre>';
      
      // wait for mermaid to load, then render
      const waitForMermaid = () => {
        if (window.mermaid && window.mermaid.run) {
          window.mermaid.run();
        } else {
          setTimeout(waitForMermaid, 100);
        }
      };
      waitForMermaid();

      // product matches table
      let mRows = '';
      const catClass = { hardware: 'category-hw', software: 'category-sw', infrastructure: 'category-infra', integration: 'category-int' };
      for (const m of matches) {
        mRows += '<tr><td>' + esc(m.name) + '</td><td>' + esc(m.sku||'') + '</td>' +
          '<td class="' + (catClass[m.category]||'') + '">' + esc(m.category||'') + '</td>' +
          '<td class="quote">' + esc(m.match_reason||'') + '</td></tr>';
      }
      document.getElementById('match-count').textContent = matches.length;
      document.getElementById('match-body').innerHTML = mRows;

      // integration points
      const intSec = document.getElementById('sec-int');
      if (intPoints.length) {
        let iRows = '';
        for (const ip of intPoints) {
          iRows += '<tr><td>' + esc(ip.endpoint||ip.from||'') + '</td><td>' + esc(ip.protocol||ip.type||'') + '</td>' +
            '<td>' + esc(ip.direction||'') + '</td><td>' + esc(ip.purpose||ip.description||'') + '</td></tr>';
        }
        intSec.innerHTML = '<h3 style="margin-top:16px;">Integration Points (' + intPoints.length + ')</h3>' +
          '<table><tr><th>Endpoint</th><th>Protocol</th><th>Direction</th><th>Purpose</th></tr>' + iRows + '</table>';
      } else { intSec.innerHTML = ''; }
    """)

    return f"""<!DOCTYPE html>
<html><head>
<style>
  {_BASE_STYLES}
  .mermaid {{ background: var(--vscode-input-background, #2d2d2d); padding: 16px; border-radius: 6px; margin: 8px 0; }}
  .mermaid svg {{ max-width: 100%; }}
</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({{ startOnLoad: false, theme: 'dark', securityLevel: 'loose' }});
</script>
</head>
<body>
  <div class="header">
    <h2>Quickcharge Architecture -- Workflow Map</h2>
    <span id="badge" class="badge simulated">Simulated</span>
  </div>
  <div id="mermaid-container"><pre class="mermaid">graph TD\n    A[Loading...]</pre></div>
  <h3 style="margin-top:16px;">Matched Products (<span id="match-count">0</span>)</h3>
  <table>
    <tr><th>Product</th><th>SKU</th><th>Category</th><th>Match Reason</th></tr>
    <tbody id="match-body"></tbody>
  </table>
  <div id="sec-int"></div>
  <script>window.__INITIAL_DATA__ = {data_json};</script>
  <script>{js}</script>
</body></html>"""


def render_system_bom(data: dict[str, Any]) -> str:
    """Render generate_system_bom results as a sortable BOM table."""
    data_json = json.dumps(data, default=str)

    js = _mcp_apps_js("illumia-system-bom", """
      const src = data._source || 'unknown';
      const badge = document.getElementById('badge');
      badge.className = 'badge ' + (src === 'live' ? 'live' : 'simulated');
      badge.textContent = src === 'live' ? 'Live' : 'Simulated';

      const items = data.bom_items || [];
      const apis = data.api_integrations || [];
      const summary = data.summary || {};

      // stats
      document.getElementById('stat-hw').textContent = summary.total_hardware_items || 0;
      document.getElementById('stat-sw').textContent = summary.total_software_items || 0;
      document.getElementById('stat-int').textContent = summary.total_integrations || 0;
      document.getElementById('stat-cx').textContent = summary.estimated_complexity || '';

      // BOM rows
      const catClass = { hardware: 'category-hw', software: 'category-sw', infrastructure: 'category-infra', integration: 'category-int' };
      let bRows = '';
      for (const b of items) {
        const deps = (b.dependencies || []).join(', ');
        bRows += '<tr><td>' + esc(b.item) + '</td><td class="' + (catClass[b.category]||'') + '">' + esc(b.category||'') + '</td>' +
          '<td style="text-align:center;font-weight:700;">' + (b.quantity||1) + '</td>' +
          '<td class="quote">' + esc(b.unit_context||'') + '</td>' +
          '<td style="font-size:11px;">' + esc(deps) + '</td></tr>';
      }
      document.getElementById('bom-body').innerHTML = bRows;

      // API integrations
      const apiSec = document.getElementById('sec-api');
      if (apis.length) {
        let aRows = '';
        for (const a of apis) {
          aRows += '<tr><td>' + esc(a.endpoint||a.from||'') + '</td><td>' + esc(a.protocol||a.type||'') + '</td>' +
            '<td>' + esc(a.auth_method||'') + '</td><td>' + esc(a.direction||'') + '</td>' +
            '<td>' + esc(a.purpose||a.description||'') + '</td></tr>';
        }
        apiSec.innerHTML = '<h3 style="margin-top:16px;">API Integrations</h3>' +
          '<table><tr><th>Endpoint</th><th>Protocol</th><th>Auth</th><th>Direction</th><th>Purpose</th></tr>' + aRows + '</table>';
      } else { apiSec.innerHTML = ''; }
    """)

    return f"""<!DOCTYPE html>
<html><head><style>{_BASE_STYLES}</style></head>
<body>
  <div class="header">
    <h2>System Bill of Materials</h2>
    <span id="badge" class="badge simulated">Simulated</span>
  </div>
  <div class="stats">
    <div class="stat-card"><div class="label">Hardware</div><div class="value" id="stat-hw">0</div></div>
    <div class="stat-card"><div class="label">Software</div><div class="value" id="stat-sw">0</div></div>
    <div class="stat-card"><div class="label">Integrations</div><div class="value" id="stat-int">0</div></div>
    <div class="stat-card"><div class="label">Complexity</div><div class="value" id="stat-cx" style="font-size:14px;"></div></div>
  </div>
  <h3>BOM Items</h3>
  <table>
    <tr><th>Item</th><th>Category</th><th>Qty</th><th>Context</th><th>Dependencies</th></tr>
    <tbody id="bom-body"></tbody>
  </table>
  <div id="sec-api"></div>
  <script>window.__INITIAL_DATA__ = {data_json};</script>
  <script>{js}</script>
</body></html>"""


def render_cross_sell_dashboard(data: dict[str, Any]) -> str:
    """Render detect_cross_sell_leads results as lead cards."""
    data_json = json.dumps(data, default=str)

    js = _mcp_apps_js("illumia-cross-sell", """
      const src = data._source || 'unknown';
      const badge = document.getElementById('badge');
      badge.className = 'badge ' + (src === 'live' ? 'live' : 'simulated');
      badge.textContent = src === 'live' ? 'Live' : 'Simulated';

      const leads = data.leads || [];
      const lines = new Set(leads.map(l => l.product_line));

      document.getElementById('stat-leads').textContent = leads.length;
      document.getElementById('stat-lines').textContent = lines.size;

      const colors = { 'Campus ID': '#4299e1', 'Campus Commerce': '#48bb78', 'Integrated Payments': '#ed8936' };

      let html = '';
      if (leads.length === 0) {
        html = '<div class="card"><p>No cross-sell triggers detected in the discovery notes.</p></div>';
      }
      for (const l of leads) {
        const c = colors[l.product_line] || '#a0aec0';
        html += '<div class="card" style="border-left:4px solid ' + c + ';">' +
          '<div style="display:flex;justify-content:space-between;align-items:start;">' +
          '<h3>' + esc(l.product_name||'') + '</h3>' +
          '<span class="tag" style="background:' + c + '22;color:' + c + ';">' + esc(l.product_line||'') + '</span></div>' +
          '<p style="margin-top:6px;"><strong>Trigger:</strong> <span class="quote">"' + esc(l.trigger_quote||l.trigger||'') + '"</span></p>' +
          (l.lead_type ? '<p style="margin-top:6px;"><strong>Lead Type:</strong> ' + esc(l.lead_type) + '</p>' : '') +
          '<p style="margin-top:6px;">' + esc(l.gap_analysis||'') + '</p>' +
          '<p style="margin-top:8px;font-size:11px;opacity:0.8;"><strong>Action:</strong> ' + esc(l.recommended_action||'') + '</p></div>';
      }
      document.getElementById('lead-cards').innerHTML = html;
    """)

    return f"""<!DOCTYPE html>
<html><head><style>{_BASE_STYLES}</style></head>
<body>
  <div class="header">
    <h2>Cross-Sell Leads</h2>
    <span id="badge" class="badge simulated">Simulated</span>
  </div>
  <div class="stats">
    <div class="stat-card"><div class="label">Leads Found</div><div class="value" id="stat-leads">0</div></div>
    <div class="stat-card"><div class="label">Product Lines</div><div class="value" id="stat-lines">0</div></div>
  </div>
  <div id="lead-cards"></div>
  <script>window.__INITIAL_DATA__ = {data_json};</script>
  <script>{js}</script>
</body></html>"""


def render_docs_panel(data: dict[str, Any]) -> str:
    """Render query_illumia_docs results."""
    data_json = json.dumps(data, default=str)

    js = _mcp_apps_js("illumia-docs", """
      const src = data._source || 'unknown';
      const badge = document.getElementById('badge');
      badge.className = 'badge ' + (src === 'live' ? 'live' : 'simulated');
      badge.textContent = src === 'live' ? 'Live' : 'Simulated';

      document.getElementById('question').textContent = data.question || '';
      const doc = (data.documentation || 'No documentation loaded.').substring(0, 5000);
      document.getElementById('docs-content').textContent = doc;
    """)

    return f"""<!DOCTYPE html>
<html><head>
<style>
  {_BASE_STYLES}
  .docs-content {{ background: var(--vscode-input-background, #2d2d2d); padding: 12px; border-radius: 6px; white-space: pre-wrap; font-size: 12px; line-height: 1.6; max-height: 400px; overflow-y: auto; }}
</style>
</head>
<body>
  <div class="header">
    <h2>Illumia Documentation</h2>
    <span id="badge" class="badge simulated">Simulated</span>
  </div>
  <div class="card">
    <h3>Question</h3>
    <p id="question"></p>
  </div>
  <div class="docs-content" id="docs-content"></div>
  <script>window.__INITIAL_DATA__ = {data_json};</script>
  <script>{js}</script>
</body></html>"""
