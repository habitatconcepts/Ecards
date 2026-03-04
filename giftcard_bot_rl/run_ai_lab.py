import streamlit as st
import asyncio, threading, time
import matplotlib.pyplot as plt
from simulator.rl_engine import simulate_strategy
from simulator.rl_queue import RLQueue
from simulator.rl_state import RLState
from simulator.ai_manager import AIManager

st.set_page_config(page_title="AI‑Tuned Arbitrage Lab", layout="wide")

strategies = ["Risk‑Averse", "Balanced", "Aggressive"]

# Shared parameter structure — AI adjusts this live
param_ref = {
    "Risk‑Averse":  {"volatility": 0.4, "roi_target": (10, 25), "speed": 1.0},
    "Balanced":     {"volatility": 0.7, "roi_target": (15, 35), "speed": 1.5},
    "Aggressive":   {"volatility": 1.0, "roi_target": (20, 60), "speed": 1.8},
}

state = RLState()
queue = RLQueue()
ai = AIManager(param_ref)

# Background coroutine runner
def launch_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(queue.launch(strategies, param_ref, simulate_strategy))

# --- Streamlit Layout ---
st.title("🤖 Reinforcement Learning Strategy Manager (Simulation)")

start, stop = st.columns(2)

if not state.running:
    if start.button("▶️ Start AI Simulation"):
        state.running = True
        t = threading.Thread(target=launch_async, daemon=True)
        t.start()
        st.toast("AI simulation running...")

if state.running:
    if stop.button("⏹ Stop"):
        queue.stop()
        state.running = False
        st.toast("Stopped AI session.")

chart_placeholder = st.empty()
param_placeholder = st.empty()

# --- RL Feedback Loop ---
while True:
    new = asyncio.run(queue.consume())
    state.update(new)
    summaries = state.summary()

    # AI observes summaries and adjusts parameters every few iterations
    if summaries is not None:
        ai.observe(summaries)
        ai.adjust_params()

        with param_placeholder.container():
            st.markdown("### 🔧 Current Parameters (AI‑tuned)")
            st.dataframe(
                [
                    {"Strategy": s,
                     "Volatility": round(param_ref[s]["volatility"], 2),
                     "ROI Range": f"{param_ref[s]['roi_target'][0]:.1f}–{param_ref[s]['roi_target'][1]:.1f}%",
                     "Speed": round(param_ref[s]["speed"], 2)}
                    for s in strategies
                ]
            )

        with chart_placeholder.container():
            fig, ax = plt.subplots(figsize=(8, 4))
            for s in strategies:
                subset = state.df[state.df["strategy"] == s]
                if not subset.empty:
                    ax.plot(subset["deal_id"], subset["roi"], ".-", label=s)
            ax.set_xlabel("Deal #")
            ax.set_ylabel("ROI (%)")
            ax.set_title("AI‑Tuned Strategy ROI Evolution")
            ax.legend()
            st.pyplot(fig)

    if state.running:
        time.sleep(1.5)
        st.experimental_rerun()
    else:
        break
