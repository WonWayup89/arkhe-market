import streamlit as st
import json

st.set_page_config(page_title="Arkeh Holdings - Constellation Geoms", layout="wide", initial_sidebar_state="expanded")

# Arkeh Holdings neon teal theme
st.markdown("""
<style>
    .main { background-color: #0a0a0a; }
    .stApp { background: linear-gradient(180deg, #0a0a0a, #1a1a2e); }
    .glow { text-shadow: 0 0 20px #5BFFE8, 0 0 40px #5BFFE8; }
    .stButton>button {
        background: linear-gradient(90deg, #5BFFE8, #00f5ff);
        color: black;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("ARKEH HOLDINGS")
st.markdown("<h2 class='glow'>Constellation Geoms - Interactive Swarm Intelligence</h2>", unsafe_allow_html=True)
st.caption("Shield. Structure. Launch. | Every relation visualized")

# Constellation data (nodes + edges)
nodes = [
    {"id": "Supervisor", "group": 1, "size": 42, "color": "#5BFFE8"},
    {"id": "Technical", "group": 2, "size": 24},
    {"id": "Volatility", "group": 2, "size": 24},
    {"id": "Regime", "group": 2, "size": 24},
    {"id": "Sentiment", "group": 2, "size": 24},
    {"id": "Risk", "group": 2, "size": 28},
    {"id": "MLExpert", "group": 2, "size": 26},
    {"id": "Crypto", "group": 3, "size": 22},
    {"id": "Stocks", "group": 3, "size": 22},
    {"id": "Futures", "group": 3, "size": 22},
    {"id": "Swarm", "group": 4, "size": 30}
]

edges = [
    {"source": "Technical", "target": "Supervisor", "value": 9},
    {"source": "Volatility", "target": "Supervisor", "value": 8},
    {"source": "Regime", "target": "Supervisor", "value": 10},
    {"source": "Sentiment", "target": "Supervisor", "value": 7},
    {"source": "Risk", "target": "Supervisor", "value": 12},
    {"source": "MLExpert", "target": "Supervisor", "value": 11},
    {"source": "Crypto", "target": "Supervisor", "value": 6},
    {"source": "Stocks", "target": "Supervisor", "value": 6},
    {"source": "Futures", "target": "Supervisor", "value": 6},
    {"source": "Supervisor", "target": "Swarm", "value": 10}
]

# Full interactive D3.js Constellation Graph
graph_html = f"""
<div id='constellation-container' style='width:100%; height:680px; background:#0a0a0a; border: 2px solid #5BFFE8; border-radius: 16px; overflow:hidden; position:relative;'>
  <svg id='constellation' width='100%' height='100%'></svg>
</div>

<script src='https://d3js.org/d3.v7.min.js'></script>
<script>
  const nodes = {json.dumps(nodes)};
  const links = {json.dumps(edges)};

  const container = document.getElementById('constellation-container');
  const width = container.clientWidth;
  const height = 680;

  const svg = d3.select("#constellation")
    .attr("viewBox", `0 0 ${{width}} ${{height}}`);

  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(130))
    .force("charge", d3.forceManyBody().strength(-1200))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(d => (d.size || 25) * 0.7));

  // Links
  const link = svg.append("g")
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke", "#5BFFE8")
    .attr("stroke-opacity", 0.7)
    .attr("stroke-width", d => Math.sqrt(d.value));

  // Nodes
  const node = svg.append("g")
    .selectAll("circle")
    .data(nodes)
    .join("circle")
    .attr("r", d => d.size / 2)
    .attr("fill", d => d.color || "#00f5ff")
    .attr("stroke", "#ffffff")
    .attr("stroke-width", 3)
    .call(d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended));

  // Labels
  const label = svg.append("g")
    .selectAll("text")
    .data(nodes)
    .join("text")
    .text(d => d.id)
    .attr("font-size", "15px")
    .attr("fill", "#ffffff")
    .attr("text-anchor", "middle")
    .attr("dy", 28);

  function dragstarted(event) {{
    if (!event.active) simulation.alphaTarget(0.3).restart();
    event.subject.fx = event.subject.x;
    event.subject.fy = event.subject.y;
  }}

  function dragged(event) {{
    event.subject.fx = event.x;
    event.subject.fy = event.y;
  }}

  function dragended(event) {{
    if (!event.active) simulation.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
  }}

  simulation.on("tick", () => {{
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    node
      .attr("cx", d => d.x)
      .attr("cy", d => d.y);

    label
      .attr("x", d => d.x)
      .attr("y", d => d.y);
  }});

  // Hover effects
  node.on("mouseover", function() {{
    d3.select(this).transition().attr("r", d => (d.size / 2) * 1.4);
  }}).on("mouseout", function() {{
    d3.select(this).transition().attr("r", d => d.size / 2);
  }});
</script>
"""

st.components.v1.html(graph_html, height=720)

# Status panels
col1, col2, col3 = st.columns(3)
with col1:
    st.success("🛡️ Supervisor Active")
    st.metric("Local Strategy Score", "94.7", "↑ 4.2")
with col2:
    st.info("🌐 Global Consensus")
    st.metric("Global Score", "88.3")
with col3:
    st.warning("📡 Swarm Reports")
    st.metric("Reports Sent Today", "3")

st.button("🔄 Refresh Constellation", type="primary", use_container_width=True)

st.caption("Drag any node • Hover for connections • Real-time swarm intelligence visualization")
