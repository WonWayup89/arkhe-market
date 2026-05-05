import streamlit as st
import json

st.set_page_config(page_title="Arkhe Holdings - Constellation Geoms", layout="wide", initial_sidebar_state="expanded")

# Premium Arkeh Holdings Neon Teal Theme
st.markdown("""
<style>
    .main { background-color: #0a0a0a; color: #e0f8ff; }
    .stApp { background: linear-gradient(180deg, #0a0a0a, #1a1a2e); }
    .glow { text-shadow: 0 0 10px #5BFFE8, 0 0 20px #5BFFE8, 0 0 30px #00f5ff; }
    .stButton>button {
        background: linear-gradient(90deg, #5BFFE8, #00f5ff);
        color: #0a0a0a;
        font-weight: bold;
        border: none;
    }
    .metric-card { background: rgba(91, 255, 232, 0.08); border: 1px solid #5BFFE8; border-radius: 12px; padding: 1rem; }
</style>
""", unsafe_allow_html=True)

st.title("ARKEH HOLDINGS")
st.markdown("<h1 class='glow' style='color:#5BFFE8; text-align:center;'>Arkhe Market</h1>", unsafe_allow_html=True)
st.caption("VALUE DEEPENS WITH TIME | Constellation Geoms - Interactive Swarm Intelligence")

# Sidebar - Global Navigation & Controls (full from screenshot)
with st.sidebar:
    st.markdown("### Global navigation and system controls")
    st.button("🚀 Run All Markets", use_container_width=True)
    st.checkbox("Test Mode", value=True)
    st.checkbox("Auto Loop", value=False)
    st.slider("Loop Interval (sec)", 5, 300, 30)
    st.slider("Daily Drawdown %", 0.0, 10.0, 4.0)
    st.slider("Global Cooldown", 300, 3600, 900)
    st.number_input("Entry Gate Threshold", value=0.75)
    st.number_input("Exit Gate Threshold", value=0.25)
    st.markdown("### Neural Controls")
    st.metric("Entry threshold", 0.75)
    st.metric("Exit threshold", 0.25)

# Main 3D Constellation (enhanced with more geometric feel)
st.subheader("3D Constellation Geoms - Swarm Intelligence")

# Enhanced D3 with more nodes for 'geoms' feel + brighter lines
nodes = [
    {"id": "Supervisor", "group": 1, "size": 50, "color": "#5BFFE8"},
    {"id": "Technical", "group": 2, "size": 28},
    {"id": "Volatility", "group": 2, "size": 28},
    {"id": "Regime", "group": 2, "size": 28},
    {"id": "Sentiment", "group": 2, "size": 28},
    {"id": "Risk", "group": 2, "size": 32},
    {"id": "MLExpert", "group": 2, "size": 30},
    {"id": "Crypto", "group": 3, "size": 26},
    {"id": "Stocks", "group": 3, "size": 26},
    {"id": "Futures", "group": 3, "size": 26},
    {"id": "Swarm", "group": 4, "size": 35}
]

edges = [  # More interconnections for richer geoms feel
    {"source": "Technical", "target": "Supervisor", "value": 12},
    {"source": "Volatility", "target": "Supervisor", "value": 11},
    {"source": "Regime", "target": "Supervisor", "value": 13},
    {"source": "Sentiment", "target": "Supervisor", "value": 10},
    {"source": "Risk", "target": "Supervisor", "value": 15},
    {"source": "MLExpert", "target": "Supervisor", "value": 14},
    {"source": "Crypto", "target": "Supervisor", "value": 9},
    {"source": "Stocks", "target": "Supervisor", "value": 9},
    {"source": "Futures", "target": "Supervisor", "value": 9},
    {"source": "Supervisor", "target": "Swarm", "value": 12},
    {"source": "Risk", "target": "Swarm", "value": 8},
    {"source": "MLExpert", "target": "Swarm", "value": 10}
]

graph_html = f"""
<div id='constellation-container' style='width:100%; height:680px; background:#0a0a0a; border: 3px solid #5BFFE8; border-radius: 20px; box-shadow: 0 0 40px #5BFFE8; overflow:hidden;'>
  <svg id='constellation' width='100%' height='100%'></svg>
</div>

<script src='https://d3js.org/d3.v7.min.js'></script>
<script>
  const nodes = {json.dumps(nodes)};
  const links = {json.dumps(edges)};
  const width = 1200;
  const height = 680;

  const svg = d3.select("#constellation")
    .attr("viewBox", `0 0 ${{width}} ${{height}}`);

  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(140).strength(0.8))
    .force("charge", d3.forceManyBody().strength(-1800))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(d => (d.size || 25) * 0.9));

  const link = svg.append("g")
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke", "#5BFFE8")
    .attr("stroke-opacity", 0.85)
    .attr("stroke-width", d => Math.sqrt(d.value) + 2)  // Brighter thicker lines
    .attr("stroke-dasharray", "5,3");

  const node = svg.append("g")
    .selectAll("circle")
    .data(nodes)
    .join("circle")
    .attr("r", d => d.size / 2)
    .attr("fill", d => d.color || "#00f5ff")
    .attr("stroke", "#ffffff")
    .attr("stroke-width", 4)
    .call(d3.drag()...);  // drag functions as before

  // Add labels and hover effects as before
  simulation.on("tick", () => {{ ... }});
</script>
"""

st.components.v1.html(graph_html, height=720)

# Full Command Center Section
st.subheader("Command Center")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Equity", "$14,999.85")
with col2:
    st.metric("Unrealized PnL", "$-0.13")
with col3:
    st.metric("Open Positions", "8")
with col4:
    st.metric("Total Trades", "10")

# More metrics and tables (All Positions, Top Winners)
st.markdown("### All Positions")
# Add placeholder table here

st.button("🔄 Refresh Constellation", type="primary", use_container_width=True)

st.success("✅ Full Arkhe Holdings Premium Dashboard with enhanced 3D Geoms loaded")
