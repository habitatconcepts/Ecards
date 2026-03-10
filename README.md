# Ecards — AI-Tuned Gift Card Arbitrage Lab

A **Streamlit web app** that simulates a reinforcement learning (RL) strategy manager for gift card arbitrage trading. Three strategies run concurrently, and an adaptive AI tuner adjusts their parameters in real time based on rolling performance rewards.

> This is a **simulation only** — no real exchange or API connections are made.

---

## Screenshots

> Save your own screenshots to `docs/screenshots/` and link them here.
>
> **Idle state** — before starting:
> ![Idle](docs/screenshots/app_idle.png)
>
> **Running state** — ROI chart + AI-tuned parameters table:
> ![Running](docs/screenshots/app_running.png)

---

## Features

- **3 concurrent trading strategies**: Risk-Averse, Balanced, Aggressive
- **Live ROI chart** updated every 1.5 seconds
- **AI parameter tuner** (`AIManager`) — adjusts volatility, speed, and ROI target range based on a weighted reward signal
- **Start / Stop / Reset** controls
- Rolling 300-record state window to keep memory bounded

---

## Prerequisites

- Python **3.10+**
- A virtual environment (recommended)

---

## Setup & Launch

```bash
# 1. Clone the repo
git clone https://github.com/your-username/Ecards.git
cd Ecards

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run giftcard_bot_rl/run_ai_lab.py
```

The app opens automatically at **http://localhost:8501**.

---

## Project Structure

```
giftcard_bot_rl/
├── run_ai_lab.py          # Streamlit UI — charts, controls, auto-refresh
└── simulator/
    ├── rl_engine.py       # Async trade generator (Gaussian ROI noise)
    ├── rl_queue.py        # Async queue — one producer task per strategy
    ├── rl_state.py        # Rolling DataFrame state (buffered concat, 300-row cap)
    └── ai_manager.py      # Adaptive RL tuner (deque memory, itertuples observe)
```

---

## How It Works

1. **`rl_engine.py`** — Each strategy runs as an `asyncio` coroutine, emitting simulated trades with Gaussian-distributed ROI noise and configurable volatility/speed.
2. **`rl_queue.py`** — An `asyncio.Queue` bridges the background thread and the Streamlit render loop. Items are drained with `get_nowait()` (non-blocking).
3. **`rl_state.py`** — Incoming records are buffered in a list and flushed to a pandas DataFrame in batches of 20, trimmed to the last 300 rows.
4. **`ai_manager.py`** — After each render cycle, the AI observes per-strategy summary stats and computes a reward (`0.7 × avg ROI + 0.3 × avg profit`). If reward < 15 it increases exploration (higher volatility, lower speed); if reward > 25 it exploits (lower volatility, higher speed). ROI targets drift slowly with Gaussian noise.
5. **`run_ai_lab.py`** — All stateful objects (`RLState`, `RLQueue`, `AIManager`, `param_ref`) are stored in `st.session_state` so they survive Streamlit's per-interaction reruns. A single background thread owns the async event loop.

---

## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI and auto-refresh |
| `matplotlib` | ROI evolution chart (Agg backend for thread safety) |
| `pandas` | Trade DataFrame and groupby summaries |
