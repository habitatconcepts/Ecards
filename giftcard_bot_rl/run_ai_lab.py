import streamlit as st
import asyncio
import threading
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from simulator.rl_engine import simulate_strategy
from simulator.rl_queue import RLQueue
from simulator.rl_state import RLState
from simulator.ai_manager import AIManager

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Arbitrage AI Lab",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ---- Base ---- */
[data-testid="stAppViewContainer"] {
    background: #0d1117;
    color: #e6edf3;
}
[data-testid="stSidebar"] {
    background: #161b22;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] * { color: #e6edf3 !important; }

/* ---- Metric cards ---- */
.kpi-row { display: flex; gap: 16px; margin-bottom: 20px; }
.kpi-card {
    flex: 1;
    background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
}
.kpi-label { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.08em; }
.kpi-value { font-size: 2rem; font-weight: 700; color: #58a6ff; margin: 4px 0 0; }
.kpi-value.green  { color: #3fb950; }
.kpi-value.yellow { color: #d29922; }
.kpi-value.purple { color: #bc8cff; }

/* ---- Status badge ---- */
.badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.badge-live { background: #1a3a2a; color: #3fb950; border: 1px solid #3fb950; }
.badge-idle { background: #2a1a1a; color: #f85149; border: 1px solid #f85149; }

/* ---- Strategy cards ---- */
.strat-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 10px;
}
.strat-title { font-size: 1rem; font-weight: 700; margin-bottom: 12px; }
.strat-row { display: flex; justify-content: space-between; font-size: 0.82rem; color: #8b949e; margin-bottom: 6px; }
.strat-val { color: #e6edf3; font-weight: 600; }

/* ---- Progress bar override ---- */
div[data-testid="stProgress"] > div > div { background-color: #58a6ff !important; }

/* ---- Tabs ---- */
button[data-baseweb="tab"] { color: #8b949e !important; }
button[data-baseweb="tab"][aria-selected="true"] { color: #58a6ff !important; border-bottom: 2px solid #58a6ff !important; }

/* ---- Dataframe ---- */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ---- Buttons ---- */
button[kind="primary"] { background: #238636 !important; border-color: #238636 !important; }

/* ---- Header divider ---- */
hr { border-color: #30363d; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
STRATEGIES = ["Risk-Averse", "Balanced", "Aggressive"]
STRATEGY_COLORS = {"Risk-Averse": "#58a6ff", "Balanced": "#3fb950", "Aggressive": "#f78166"}

DEFAULT_PARAMS = {
    "Risk-Averse":  {"volatility": 0.4, "roi_target": (10, 25), "speed": 1.0},
    "Balanced":     {"volatility": 0.7, "roi_target": (15, 35), "speed": 1.5},
    "Aggressive":   {"volatility": 1.0, "roi_target": (20, 60), "speed": 1.8},
}

# ── Session state ─────────────────────────────────────────────────────────────
for key, val in [
    ("param_ref",      {k: dict(v) for k, v in DEFAULT_PARAMS.items()}),
    ("state",          RLState()),
    ("queue",          RLQueue()),
    ("ai",             None),
    ("thread_started", False),
    ("start_time",     None),
]:
    if key not in st.session_state:
        st.session_state[key] = val

if st.session_state.ai is None:
    st.session_state.ai = AIManager(st.session_state.param_ref)

state     = st.session_state.state
queue     = st.session_state.queue
ai        = st.session_state.ai
param_ref = st.session_state.param_ref


def launch_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(queue.launch(STRATEGIES, param_ref, simulate_strategy))


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    demo_mode = st.toggle("🧪 Demo Mode (mock data)", value=False,
                          help="Instantly fills the simulation with fake trade data "
                               "so you can preview the UI without starting the live engine.")
    refresh_rate = st.slider("Refresh interval (s)", 0.5, 5.0, 1.5, 0.5)
    chart_window = st.slider("Chart history (deals)", 50, 300, 150, 25)
    st.markdown("---")

    st.markdown("### 📖 Strategy Guide")
    for s, color in STRATEGY_COLORS.items():
        p = param_ref[s]
        st.markdown(
            f"<div class='strat-card'>"
            f"<div class='strat-title' style='color:{color}'>{s}</div>"
            f"<div class='strat-row'><span>Volatility</span><span class='strat-val'>{p['volatility']:.2f}</span></div>"
            f"<div class='strat-row'><span>ROI Target</span><span class='strat-val'>{p['roi_target'][0]:.0f}–{p['roi_target'][1]:.0f}%</span></div>"
            f"<div class='strat-row'><span>Speed</span><span class='strat-val'>{p['speed']:.2f}</span></div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.caption("Gift Card Arbitrage Simulator · v2.0")


# ── Header ────────────────────────────────────────────────────────────────────
hcol1, hcol2 = st.columns([5, 1])
with hcol1:
    st.markdown("# 📈 Arbitrage AI Lab")
    st.caption("Reinforcement learning strategy manager — live parameter adaptation simulation")
with hcol2:
    badge = (
        "<span class='badge badge-live'>● LIVE</span>"
        if state.running else
        "<span class='badge badge-idle'>● IDLE</span>"
    )
    st.markdown(f"<div style='padding-top:28px;text-align:right'>{badge}</div>", unsafe_allow_html=True)

st.markdown("---")

# ── Controls ──────────────────────────────────────────────────────────────────
ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 2, 2, 6])

if not state.running:
    if ctrl1.button("▶️ Start", use_container_width=True, type="primary"):
        state.running = True
        if not st.session_state.thread_started:
            threading.Thread(target=launch_async, daemon=True).start()
            st.session_state.thread_started = True
        st.session_state.start_time = time.time()
        st.toast("Simulation started", icon="🚀")
        st.rerun()

if state.running:
    if ctrl2.button("⏹ Stop", use_container_width=True):
        queue.stop()
        state.running = False
        st.session_state.thread_started = False
        st.toast("Simulation stopped", icon="🛑")
        st.rerun()

if ctrl3.button("🔄 Reset", use_container_width=True):
    queue.stop()
    st.session_state.clear()
    st.rerun()

# ── Mock data injection (Demo Mode) ──────────────────────────────────────────
if demo_mode and state.df.empty:
    import random as _rng
    from datetime import datetime as _dt
    _mock = []
    _deal_counters = {s: 0 for s in STRATEGIES}
    for _ in range(120):
        s = _rng.choice(STRATEGIES)
        _deal_counters[s] += 1
        p     = DEFAULT_PARAMS[s]
        roi   = max(0.0, min(_rng.gauss(_rng.uniform(*p["roi_target"]), 10 * p["volatility"]), 80.0))
        fv    = _rng.choice([50, 100, 150, 200])
        _mock.append({
            "timestamp": _dt.now().strftime("%H:%M:%S"),
            "strategy":  s,
            "deal_id":   _deal_counters[s],
            "roi":       round(roi, 2),
            "profit":    round(fv * roi / 100, 2),
        })
    state.update(_mock)
    state._flush()

# ── Consume new data ──────────────────────────────────────────────────────────
if state.running:
    new = queue.consume()   # synchronous — thread-safe stdlib queue.Queue
    state.update(new)

summaries = state.summary()
totals    = state.totals()
recent    = state.recent_trades(15)

# ── KPI row ───────────────────────────────────────────────────────────────────
if totals:
    elapsed = ""
    if st.session_state.start_time:
        secs = int(time.time() - st.session_state.start_time)
        elapsed = f"{secs // 60:02d}:{secs % 60:02d}"

    st.markdown(
        f"""<div class='kpi-row'>
          <div class='kpi-card'>
            <div class='kpi-label'>Total Deals</div>
            <div class='kpi-value'>{totals['total_deals']}</div>
          </div>
          <div class='kpi-card'>
            <div class='kpi-label'>Avg ROI</div>
            <div class='kpi-value green'>{totals['avg_roi']:.1f}%</div>
          </div>
          <div class='kpi-card'>
            <div class='kpi-label'>Total Profit</div>
            <div class='kpi-value yellow'>${totals['total_profit']:,.2f}</div>
          </div>
          <div class='kpi-card'>
            <div class='kpi-label'>Best Strategy</div>
            <div class='kpi-value purple'>{totals['best_strategy']}</div>
          </div>
          <div class='kpi-card'>
            <div class='kpi-label'>Session Time</div>
            <div class='kpi-value'>{elapsed or "—"}</div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """<div class='kpi-row'>
          <div class='kpi-card'><div class='kpi-label'>Total Deals</div><div class='kpi-value'>—</div></div>
          <div class='kpi-card'><div class='kpi-label'>Avg ROI</div><div class='kpi-value green'>—</div></div>
          <div class='kpi-card'><div class='kpi-label'>Total Profit</div><div class='kpi-value yellow'>—</div></div>
          <div class='kpi-card'><div class='kpi-label'>Best Strategy</div><div class='kpi-value purple'>—</div></div>
          <div class='kpi-card'><div class='kpi-label'>Session Time</div><div class='kpi-value'>—</div></div>
        </div>""",
        unsafe_allow_html=True,
    )

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_chart, tab_params, tab_feed = st.tabs(["📈 Live Chart", "🔧 AI Parameters", "📋 Trade Feed"])

# ── Tab 1: Chart ──────────────────────────────────────────────────────────────
with tab_chart:
    chart_ph = st.empty()
    if summaries is not None:
        with chart_ph.container():
            fig, ax = plt.subplots(figsize=(12, 4), facecolor="#0d1117")
            ax.set_facecolor("#0d1117")
            for spine in ax.spines.values():
                spine.set_edgecolor("#30363d")
            ax.tick_params(colors="#8b949e")
            ax.xaxis.label.set_color("#8b949e")
            ax.yaxis.label.set_color("#8b949e")
            ax.title.set_color("#e6edf3")
            ax.grid(True, color="#21262d", linewidth=0.8, linestyle="--")

            for s in STRATEGIES:
                subset = state.df[state.df["strategy"] == s].tail(chart_window)
                if not subset.empty:
                    ax.plot(
                        subset["deal_id"], subset["roi"],
                        "-", label=s, linewidth=1.8,
                        color=STRATEGY_COLORS[s], alpha=0.9,
                    )
                    # Smoothed average line
                    if len(subset) >= 5:
                        rolled = subset["roi"].rolling(5).mean()
                        ax.plot(subset["deal_id"], rolled, "--",
                                color=STRATEGY_COLORS[s], linewidth=1, alpha=0.5)

            ax.set_xlabel("Deal #", fontsize=9)
            ax.set_ylabel("ROI (%)", fontsize=9)
            ax.set_title("ROI Evolution by Strategy (— live  ·  ‐‐ 5-deal avg)", fontsize=11)
            ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
            ax.legend(facecolor="#161b22", edgecolor="#30363d", labelcolor="#e6edf3", fontsize=9)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
    else:
        st.markdown(
            "<div style='text-align:center;padding:60px;color:#8b949e;font-size:1.1rem'>"
            "Press <strong>▶️ Start</strong> to see the live chart.</div>",
            unsafe_allow_html=True,
        )

# ── Tab 2: Parameters ─────────────────────────────────────────────────────────
with tab_params:
    if summaries is not None:
        ai.observe(summaries)
        ai.adjust_params()

        cols = st.columns(3)
        for i, s in enumerate(STRATEGIES):
            p = param_ref[s]
            color = STRATEGY_COLORS[s]
            # Per-strategy summary stat
            row = summaries[summaries["strategy"] == s]
            avg_roi   = float(row["roi"].values[0])   if len(row) else 0.0
            tot_profit = float(row["profit"].values[0]) if len(row) else 0.0

            with cols[i]:
                st.markdown(
                    f"<div class='strat-card'>"
                    f"<div class='strat-title' style='color:{color}'>{s}</div>"
                    f"<div class='strat-row'><span>Volatility</span><span class='strat-val'>{p['volatility']:.2f}</span></div>"
                    f"<div class='strat-row'><span>ROI Target</span><span class='strat-val'>{p['roi_target'][0]:.1f}–{p['roi_target'][1]:.1f}%</span></div>"
                    f"<div class='strat-row'><span>Speed</span><span class='strat-val'>{p['speed']:.2f}</span></div>"
                    f"<div class='strat-row'><span>Avg ROI</span><span class='strat-val' style='color:{color}'>{avg_roi:.1f}%</span></div>"
                    f"<div class='strat-row'><span>Total Profit</span><span class='strat-val'>${tot_profit:,.2f}</span></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.caption("Volatility level")
                st.progress(min(1.0, p["volatility"] / 2.0))
                st.caption("Speed")
                st.progress(min(1.0, p["speed"] / 3.0))

        st.markdown("---")
        st.markdown("#### Full Parameter Table")
        st.dataframe(
            pd.DataFrame([
                {
                    "Strategy":   s,
                    "Volatility": round(param_ref[s]["volatility"], 3),
                    "ROI Low":    round(param_ref[s]["roi_target"][0], 1),
                    "ROI High":   round(param_ref[s]["roi_target"][1], 1),
                    "Speed":      round(param_ref[s]["speed"], 2),
                }
                for s in STRATEGIES
            ]),
            width="stretch",
            hide_index=True,
        )
    else:
        st.markdown(
            "<div style='text-align:center;padding:60px;color:#8b949e;font-size:1.1rem'>"
            "No data yet — start the simulation to see AI-tuned parameters.</div>",
            unsafe_allow_html=True,
        )

# ── Tab 3: Trade Feed ─────────────────────────────────────────────────────────
with tab_feed:
    if recent is not None:
        # Colour-coded ROI column
        def colour_roi(val):
            if val >= 30:
                return "color: #3fb950; font-weight:600"
            elif val >= 15:
                return "color: #d29922; font-weight:600"
            else:
                return "color: #f85149;"

        styled = (
            recent
            .rename(columns={"timestamp": "Time", "strategy": "Strategy",
                              "roi": "ROI (%)", "profit": "Profit ($)"})
            .style
            .map(colour_roi, subset=["ROI (%)"])
            .format({"ROI (%)": "{:.1f}", "Profit ($)": "${:.2f}"})
        )
        st.markdown("#### 📋 Most Recent Trades")
        st.dataframe(styled, width="stretch", hide_index=True)
    else:
        st.markdown(
            "<div style='text-align:center;padding:60px;color:#8b949e;font-size:1.1rem'>"
            "No trades yet — start the simulation to see the live feed.</div>",
            unsafe_allow_html=True,
        )

# ── Auto-refresh ──────────────────────────────────────────────────────────────
if state.running:
    time.sleep(refresh_rate)
    st.rerun()

