import random

class AIManager:
    """Reinforcement-style adaptive parameter tuner."""

    def __init__(self, param_ref):
        self.param_ref = param_ref
        self.memory = {s: {"recent_roi": [], "recent_profit": []} for s in param_ref.keys()}

    def observe(self, summaries):
        """Receive new summary DataFrame and record rolling averages."""
        for _, row in summaries.iterrows():
            s = row["strategy"]
            self.memory[s]["recent_roi"].append(row["roi"])
            self.memory[s]["recent_profit"].append(row["profit"])
            if len(self.memory[s]["recent_roi"]) > 10:
                self.memory[s]["recent_roi"].pop(0)
                self.memory[s]["recent_profit"].pop(0)

    def reward(self, strategy):
        """Weighted average of ROI mean and profit growth as a simple reward estimate."""
        roi_vals = self.memory[strategy]["recent_roi"]
        profits = self.memory[strategy]["recent_profit"]
        if not roi_vals:
            return 0
        return 0.7 * (sum(roi_vals) / len(roi_vals)) + 0.3 * (sum(profits) / len(profits))

    def adjust_params(self):
        """Core adaptation step — nudges volatility or ROI range based on reward trends."""
        for s in self.param_ref.keys():
            r = self.reward(s)
            conf = self.param_ref[s]
            drift = random.uniform(-0.05, 0.05)
            # If reward poor, increase volatility to explore / decrease speed
            if r < 15:
                conf["volatility"] = max(0.1, conf["volatility"] + 0.1)
                conf["speed"] = max(0.5, conf["speed"] - 0.2)
            elif r > 25:
                conf["volatility"] = max(0.1, conf["volatility"] - 0.05)
                conf["speed"] = min(3.0, conf["speed"] + 0.1)
            # Adjust ROI target range slowly
            low, high = conf["roi_target"]
            delta = drift * 5
            conf["roi_target"] = (max(5, low + delta), min(80, high + delta))
