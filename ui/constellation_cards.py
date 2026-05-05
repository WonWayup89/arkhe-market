import streamlit as st
import streamlit.components.v1 as components


def render_crypto_constellation_card():
    html = """
    <style>
    .arkhe-constellation-card {
        position: relative;
        height: 230px;
        border: 1px solid rgba(91,255,232,0.32);
        border-radius: 22px;
        padding: 20px;
        background:
            radial-gradient(circle at 50% 35%, rgba(91,255,232,0.18), transparent 34%),
            linear-gradient(145deg, rgba(11,17,24,0.94), rgba(4,7,10,0.96));
        box-shadow: 0 0 30px rgba(91,255,232,0.10);
        overflow: hidden;
        transition: all 0.45s ease;
        font-family: Inter, Arial, sans-serif;
    }

    .arkhe-constellation-card:hover {
        height: 430px;
        box-shadow: 0 0 55px rgba(91,255,232,0.26), inset 0 0 36px rgba(91,255,232,0.07);
        border-color: rgba(91,255,232,0.72);
    }

    .arkhe-constellation-header {
        display: flex;
        justify-content: space-between;
        gap: 20px;
        position: relative;
        z-index: 4;
    }

    .arkhe-kicker {
        color: #5BFFE8;
        font-size: 11px;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        font-weight: 800;
    }

    .arkhe-title {
        color: #F7F7F2;
        font-size: 28px;
        font-weight: 850;
        margin-top: 5px;
    }

    .arkhe-subtitle {
        color: #9CA7AE;
        font-size: 14px;
        margin-top: 5px;
    }

    .arkhe-value {
        color: #F7F7F2;
        font-size: 25px;
        font-weight: 850;
        text-shadow: 0 0 18px rgba(91,255,232,0.25);
    }

    .stage {
        position: absolute;
        inset: 85px 20px 50px 20px;
        opacity: 0.58;
        transform: scale(0.72) translateY(18px);
        transform-origin: center;
        transition: all 0.55s ease;
    }

    .arkhe-constellation-card:hover .stage {
        opacity: 1;
        transform: scale(1) translateY(0);
    }

    .orbit {
        position: absolute;
        left: 50%;
        top: 50%;
        border: 1px solid rgba(91,255,232,0.22);
        border-radius: 999px;
        transform: translate(-50%, -50%);
        box-shadow: 0 0 20px rgba(91,255,232,0.08);
    }

    .orbit.one {
        width: 230px;
        height: 130px;
    }

    .orbit.two {
        width: 340px;
        height: 210px;
        transform: translate(-50%, -50%) rotate(-18deg);
    }

    .node {
        position: absolute;
        width: 54px;
        height: 54px;
        border-radius: 50%;
        display: grid;
        place-items: center;
        color: #F7F7F2;
        font-size: 12px;
        font-weight: 850;
        border: 1px solid rgba(91,255,232,0.64);
        background:
            radial-gradient(circle at 35% 30%, rgba(255,255,255,0.30), transparent 18%),
            radial-gradient(circle, rgba(91,255,232,0.34), rgba(8,12,17,0.96) 62%);
        box-shadow: 0 0 16px rgba(91,255,232,0.34), inset 0 0 12px rgba(91,255,232,0.18);
        transition: all 0.45s ease;
    }

    .node:hover {
        transform: scale(1.2);
        box-shadow: 0 0 30px rgba(91,255,232,0.75), inset 0 0 16px rgba(91,255,232,0.24);
        z-index: 5;
    }

    .core {
        left: calc(50% - 32px);
        top: calc(50% - 32px);
        width: 64px;
        height: 64px;
        color: #05090D;
        background: radial-gradient(circle, #F7F7F2, #5BFFE8 56%, #0B1118 100%);
    }

    .btc { left: 12%; top: 42%; }
    .eth { right: 12%; top: 42%; }
    .sol { left: 27%; top: 8%; }
    .xrp { right: 27%; top: 8%; }
    .ada { left: 26%; bottom: 4%; }
    .link { right: 26%; bottom: 4%; }
    .doge { left: 48%; top: -2%; }
    .avax { left: 48%; bottom: -2%; }

    .line {
        position: absolute;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(91,255,232,0.62), transparent);
        transform-origin: center;
        box-shadow: 0 0 12px rgba(91,255,232,0.42);
    }

    .a { width: 62%; left: 19%; top: 50%; }
    .b { width: 48%; left: 26%; top: 32%; transform: rotate(28deg); }
    .c { width: 48%; left: 26%; top: 66%; transform: rotate(-28deg); }
    .d { width: 36%; left: 32%; top: 50%; transform: rotate(90deg); }

    .footer {
        position: absolute;
        left: 20px;
        right: 20px;
        bottom: 16px;
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        opacity: 0;
        transform: translateY(8px);
        transition: all 0.45s ease;
    }

    .arkhe-constellation-card:hover .footer {
        opacity: 1;
        transform: translateY(0);
    }

    .footer span {
        border: 1px solid rgba(91,255,232,0.26);
        border-radius: 999px;
        padding: 6px 10px;
        color: #5BFFE8;
        background: rgba(91,255,232,0.07);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    </style>

    <div class="arkhe-constellation-card">
      <div class="arkhe-constellation-header">
        <div>
          <div class="arkhe-kicker">Market Cluster</div>
          <div class="arkhe-title">Crypto Total</div>
          <div class="arkhe-subtitle">Hover to expand the currency constellation.</div>
        </div>
        <div class="arkhe-value">$14,999.85</div>
      </div>

      <div class="stage">
        <div class="orbit one"></div>
        <div class="orbit two"></div>
        <div class="line a"></div>
        <div class="line b"></div>
        <div class="line c"></div>
        <div class="line d"></div>

        <div class="node core">A</div>
        <div class="node btc">BTC</div>
        <div class="node eth">ETH</div>
        <div class="node sol">SOL</div>
        <div class="node xrp">XRP</div>
        <div class="node ada">ADA</div>
        <div class="node link">LINK</div>
        <div class="node doge">DOGE</div>
        <div class="node avax">AVAX</div>
      </div>

      <div class="footer">
        <span>8 nodes</span>
        <span>Paper mode</span>
        <span>Neural gate active</span>
      </div>
    </div>
    """

    components.html(html, height=460)
