"""
ui/constellation.py — Reusable 3D-feel geometric web (D3 force graph).

Used at the top of multiple views to visualize relationships between things
(supervisor ↔ expert agents, market ↔ symbols, strategies ↔ tiers, etc.).

Renders an SVG force-directed graph on a transparent background so it sits
naturally inside the Arkeh Holdings hero / card aesthetic. The wireframe
icosahedrons in the Arkheholdings.net animation are evoked via:
  · pulsing concentric rings at the centroid
  · cyan node halos with radial gradients
  · animated link gradients
  · gentle continuous drift via d3-force
"""

import json
import uuid
import streamlit.components.v1 as components


def constellation_web(
    nodes,
    edges,
    *,
    height: int = 360,
    title: str | None = None,
    subtitle: str | None = None,
    accent: str = "#5BFFE8",
    show_orbits: bool = True,
):
    """
    Render an interactive constellation web.

    nodes: list of dicts: { id, group?, size?, color?, label? }
    edges: list of dicts: { source, target, value? }

    The component is fully self-contained and gets a unique element ID per
    invocation, so multiple webs can coexist on one page.
    """

    uid = "c_" + uuid.uuid4().hex[:8]
    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    orbits = "true" if show_orbits else "false"

    head_html = ""
    if title or subtitle:
        head_html = f"""
        <div class="cw-head">
          {f'<div class="cw-kicker">{title}</div>' if title else ''}
          {f'<div class="cw-sub">{subtitle}</div>' if subtitle else ''}
        </div>
        """

    html = f"""
    <div class="cw-wrap" id="{uid}-wrap">
      {head_html}
      <div class="cw-stage" id="{uid}-stage">
        <svg id="{uid}" width="100%" height="100%"></svg>
      </div>
    </div>

    <style>
      #{uid}-wrap {{
        position: relative;
        border: 1px solid rgba(91,255,232,0.28);
        border-radius: 22px;
        padding: 14px 14px 8px 14px;
        background:
            radial-gradient(circle at 50% 0%, rgba(91,255,232,0.14), transparent 38%),
            linear-gradient(145deg, rgba(11,17,24,0.92), rgba(4,7,10,0.94));
        box-shadow:
            0 0 38px rgba(91,255,232,0.10),
            inset 0 0 32px rgba(91,255,232,0.04);
        overflow: hidden;
        font-family: Inter, system-ui, -apple-system, sans-serif;
      }}
      #{uid}-wrap:before {{
        content: "";
        position: absolute; inset: 0;
        background-image:
            linear-gradient(rgba(91,255,232,0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(91,255,232,0.06) 1px, transparent 1px);
        background-size: 36px 36px;
        opacity: 0.30;
        mask-image: radial-gradient(circle at 50% 35%, black, transparent 78%);
        pointer-events: none;
      }}
      #{uid}-wrap .cw-head {{
        position: relative; z-index: 3;
        display: flex; align-items: baseline; gap: 12px;
        padding: 2px 6px 8px 6px;
      }}
      #{uid}-wrap .cw-kicker {{
        color: {accent};
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.22em;
        text-transform: uppercase;
      }}
      #{uid}-wrap .cw-sub {{
        color: #9CA7AE;
        font-size: 0.84rem;
      }}
      #{uid}-wrap .cw-stage {{
        position: relative;
        height: {height - 60}px;
        z-index: 2;
      }}
      #{uid}-wrap svg text {{
        font-family: Inter, system-ui, sans-serif;
        font-weight: 700;
        fill: #F7F7F2;
        paint-order: stroke;
        stroke: rgba(5,9,13,0.85);
        stroke-width: 3px;
      }}
    </style>

    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
    (function() {{
      const accent = "{accent}";
      const showOrbits = {orbits};
      const nodes = {nodes_json}.map(n => Object.assign({{
        size: 22, group: 1, color: accent
      }}, n));
      const links = {edges_json};

      const stage = document.getElementById("{uid}-stage");
      const svgEl = document.getElementById("{uid}");

      function size() {{
        const r = stage.getBoundingClientRect();
        return [Math.max(r.width, 320), Math.max(r.height, 240)];
      }}
      let [W, H] = size();

      const svg = d3.select(svgEl).attr("viewBox", `0 0 ${{W}} ${{H}}`);

      // Defs: glow filter + radial gradients for nodes / links
      const defs = svg.append("defs");

      const glow = defs.append("filter").attr("id", "{uid}-glow");
      glow.append("feGaussianBlur").attr("stdDeviation", "2.6").attr("result", "blur");
      const merge = glow.append("feMerge");
      merge.append("feMergeNode").attr("in", "blur");
      merge.append("feMergeNode").attr("in", "SourceGraphic");

      const grad = defs.append("radialGradient").attr("id", "{uid}-node");
      grad.append("stop").attr("offset", "0%").attr("stop-color", "#F7F7F2").attr("stop-opacity", 0.95);
      grad.append("stop").attr("offset", "55%").attr("stop-color", accent).attr("stop-opacity", 0.85);
      grad.append("stop").attr("offset", "100%").attr("stop-color", "#0B1118").attr("stop-opacity", 1);

      const linkGrad = defs.append("linearGradient")
        .attr("id", "{uid}-link").attr("x1", "0%").attr("x2", "100%");
      linkGrad.append("stop").attr("offset", "0%").attr("stop-color", accent).attr("stop-opacity", 0.0);
      linkGrad.append("stop").attr("offset", "50%").attr("stop-color", accent).attr("stop-opacity", 0.85);
      linkGrad.append("stop").attr("offset", "100%").attr("stop-color", accent).attr("stop-opacity", 0.0);

      // Concentric orbit rings (decorative wireframe vibe)
      const center = svg.append("g").attr("class", "orbits");
      if (showOrbits) {{
        for (const r of [0.30, 0.45, 0.62]) {{
          center.append("ellipse")
            .attr("cx", W/2).attr("cy", H/2)
            .attr("rx", W*r*0.55).attr("ry", H*r*0.62)
            .attr("fill", "none")
            .attr("stroke", accent)
            .attr("stroke-opacity", 0.12)
            .attr("stroke-dasharray", "1 4");
        }}
      }}

      const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(d => 90 + (d.value || 4) * 4))
        .force("charge", d3.forceManyBody().strength(-360))
        .force("center", d3.forceCenter(W/2, H/2))
        .force("collide", d3.forceCollide().radius(d => (d.size || 22) * 0.7 + 6));

      const link = svg.append("g").attr("class", "links")
        .selectAll("line").data(links).join("line")
        .attr("stroke", "url(#{uid}-link)")
        .attr("stroke-opacity", 0.85)
        .attr("stroke-width", d => Math.max(1, Math.sqrt(d.value || 4)));

      const nodeG = svg.append("g").attr("class", "nodes")
        .selectAll("g").data(nodes).join("g")
        .call(d3.drag()
          .on("start", (e, d) => {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
          .on("drag",  (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
          .on("end",   (e, d) => {{ if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }}));

      nodeG.append("circle")
        .attr("r", d => (d.size || 22) * 0.70 + 6)
        .attr("fill", "url(#{uid}-node)")
        .attr("fill-opacity", 0.18)
        .attr("stroke", accent)
        .attr("stroke-opacity", 0.45);

      nodeG.append("circle")
        .attr("r", d => (d.size || 22) * 0.46)
        .attr("fill", d => d.color || accent)
        .attr("fill-opacity", 0.85)
        .attr("stroke", "#F7F7F2")
        .attr("stroke-opacity", 0.65)
        .attr("stroke-width", 1.2)
        .attr("filter", "url(#{uid}-glow)");

      nodeG.append("text")
        .text(d => d.label || d.id)
        .attr("text-anchor", "middle")
        .attr("font-size", d => (d.size || 22) > 30 ? "13px" : "11px")
        .attr("dy", d => (d.size || 22) * 0.55 + 14);

      nodeG.on("mouseover", function() {{
        d3.select(this).select("circle:nth-child(2)").transition().duration(180)
          .attr("r", d => (d.size || 22) * 0.62);
      }}).on("mouseout", function() {{
        d3.select(this).select("circle:nth-child(2)").transition().duration(180)
          .attr("r", d => (d.size || 22) * 0.46);
      }});

      simulation.on("tick", () => {{
        link
          .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
        nodeG.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
      }});

      // Resize observer keeps the simulation centered if the panel resizes
      const ro = new ResizeObserver(() => {{
        const [w, h] = size();
        if (Math.abs(w - W) < 4 && Math.abs(h - H) < 4) return;
        W = w; H = h;
        svg.attr("viewBox", `0 0 ${{W}} ${{H}}`);
        simulation.force("center", d3.forceCenter(W/2, H/2)).alpha(0.4).restart();
      }});
      ro.observe(stage);
    }})();
    </script>
    """

    components.html(html, height=height + 12, scrolling=False)


# ── Pre-built relationship graphs for each view ──────────────────────

def system_constellation(height: int = 420):
    """Top-level system: supervisor at center, expert agents + market clusters."""
    nodes = [
        {"id": "Supervisor",  "group": 1, "size": 44, "color": "#5BFFE8"},
        # Expert agents
        {"id": "Technical",   "group": 2, "size": 26, "color": "#19C7B8"},
        {"id": "Volatility",  "group": 2, "size": 26, "color": "#19C7B8"},
        {"id": "Regime",      "group": 2, "size": 26, "color": "#19C7B8"},
        {"id": "Sentiment",   "group": 2, "size": 26, "color": "#19C7B8"},
        {"id": "Risk",        "group": 2, "size": 28, "color": "#19C7B8"},
        {"id": "ML Expert",   "group": 2, "size": 28, "color": "#C9A24A"},
        # Market clusters
        {"id": "Crypto",      "group": 3, "size": 30, "color": "#5BFFE8"},
        {"id": "Stocks",      "group": 3, "size": 30, "color": "#5BFFE8"},
        {"id": "Futures",     "group": 3, "size": 30, "color": "#5BFFE8"},
        # Pipeline
        {"id": "Promotion",   "group": 4, "size": 26, "color": "#C9A24A"},
        {"id": "Swarm",       "group": 4, "size": 30, "color": "#C9A24A"},
    ]
    edges = [
        {"source": "Technical",  "target": "Supervisor", "value": 9},
        {"source": "Volatility", "target": "Supervisor", "value": 8},
        {"source": "Regime",     "target": "Supervisor", "value": 10},
        {"source": "Sentiment",  "target": "Supervisor", "value": 7},
        {"source": "Risk",       "target": "Supervisor", "value": 12},
        {"source": "ML Expert",  "target": "Supervisor", "value": 11},
        {"source": "Crypto",     "target": "Supervisor", "value": 6},
        {"source": "Stocks",     "target": "Supervisor", "value": 6},
        {"source": "Futures",    "target": "Supervisor", "value": 6},
        {"source": "Supervisor", "target": "Promotion",  "value": 8},
        {"source": "Promotion",  "target": "Swarm",      "value": 6},
    ]
    constellation_web(
        nodes, edges,
        height=height,
        title="System Constellation",
        subtitle="Supervisor · expert agents · markets · promotion pipeline",
    )


def market_constellation(market: str, symbols, *, height: int = 320):
    """A market view: market node at center + expert agents + each symbol."""
    market_label = market.title()
    accent = {
        "crypto":  "#5BFFE8",
        "stocks":  "#19C7B8",
        "futures": "#C9A24A",
    }.get(market.lower(), "#5BFFE8")

    nodes = [
        {"id": market_label, "group": 1, "size": 44, "color": accent},
        {"id": "Technical",  "group": 2, "size": 22},
        {"id": "Volatility", "group": 2, "size": 22},
        {"id": "Regime",     "group": 2, "size": 22},
        {"id": "Sentiment",  "group": 2, "size": 22},
        {"id": "Risk",       "group": 2, "size": 24},
    ]
    for s in symbols:
        nodes.append({"id": s, "group": 3, "size": 18, "color": "#F7F7F2"})

    edges = [
        {"source": "Technical",  "target": market_label, "value": 8},
        {"source": "Volatility", "target": market_label, "value": 7},
        {"source": "Regime",     "target": market_label, "value": 9},
        {"source": "Sentiment",  "target": market_label, "value": 6},
        {"source": "Risk",       "target": market_label, "value": 11},
    ]
    for s in symbols:
        edges.append({"source": s, "target": market_label, "value": 4})

    constellation_web(
        nodes, edges,
        height=height,
        accent=accent,
        title=f"{market_label} Constellation",
        subtitle=f"{len(symbols)} symbols · 5 expert agents",
    )


def promotion_constellation(tier_summary: dict, *, height: int = 320):
    """Promotion pipeline: sim → shadow → live, with each symbol as a node."""
    nodes = [
        {"id": "Sim Only",         "group": 1, "size": 34, "color": "#9CA7AE"},
        {"id": "Shadow Validated", "group": 1, "size": 34, "color": "#C9A24A"},
        {"id": "Live Eligible",    "group": 1, "size": 36, "color": "#5BFFE8"},
    ]
    edges = [
        {"source": "Sim Only",         "target": "Shadow Validated", "value": 8},
        {"source": "Shadow Validated", "target": "Live Eligible",    "value": 8},
    ]
    for tier_key, tier_label, color in [
        ("sim_only",         "Sim Only",         "#9CA7AE"),
        ("shadow_validated", "Shadow Validated", "#C9A24A"),
        ("live_eligible",    "Live Eligible",    "#5BFFE8"),
    ]:
        for sym in (tier_summary.get(tier_key) or [])[:8]:
            sid = f"{sym}::{tier_key}"
            nodes.append({"id": sid, "label": sym, "group": 2, "size": 16, "color": color})
            edges.append({"source": sid, "target": tier_label, "value": 3})

    constellation_web(
        nodes, edges,
        height=height,
        accent="#C9A24A",
        title="Promotion Pipeline",
        subtitle="Simulation → Shadow validation → Live eligibility",
    )
