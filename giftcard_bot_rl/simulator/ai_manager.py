import random
from collections import deque

MEMORY_WINDOW = 10  # rolling window size


class AIManager:
    """Reinforcement-style adaptive parameter tuner."""

    def __init__(self, param_ref):
        self.param_ref = param_ref
        # deque(maxlen) automatically evicts the oldest entry — O(1) vs list.pop(0) O(n)
        self.memory = {
            s: {
                "recent_roi":    deque(maxlen=MEMORY_WINDOW),
                "recent_profit": deque(maxlen=MEMORY_WINDOW),
            }
            for s in param_ref
        }

    def observe(self, summaries):
        """Record latest per-strategy averages from the summary DataFrame."""
        # itertuples is ~10x faster than iterrows for row-wise access
        for row in summaries.itertuples(index=False):
            mem = self.memory.get(row.strategy)
            if mem is not None:
                mem["recent_roi"].append(row.roi)
                mem["recent_profit"].append(row.profit)

    def reward(self, strategy):
        """Weighted reward: 70% avg ROI + 30% avg profit."""
        roi_vals = self.memory[strategy]["recent_roi"]
        profits  = self.memory[strategy]["recent_profit"]
        if not roi_vals:
            return 0.0
        n = len(roi_vals)
        return 0.7 * (sum(roi_vals) / n) + 0.3 * (sum(profits) / n)

    def adjust_params(self):
        """Nudge volatility, speed, and ROI range based on rolling reward."""
        for s, conf in self.param_ref.items():
            r     = self.reward(s)
            drift = random.uniform(-0.05, 0.05)
            if r < 15:
                # Reward is poor — increase exploration, slow down
                conf["volatility"] = min(2.0, conf["volatility"] + 0.1)
                conf["speed"]      = max(0.5, conf["speed"]      - 0.2)
            elif r > 25:
                # Reward is good — exploit more, speed up
                conf["volatility"] = max(0.1, conf["volatility"] - 0.05)
                conf["speed"]      = min(3.0, conf["speed"]      + 0.1)
            # Drift ROI targets slowly
            low, high = conf["roi_target"]
            delta = drift * 5
            conf["roi_target"] = (max(5, low + delta), min(80, high + delta))
