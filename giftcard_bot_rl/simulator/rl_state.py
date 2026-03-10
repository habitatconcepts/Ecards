import pandas as pd

COLS       = ["timestamp", "strategy", "deal_id", "roi", "profit"]
MAX_ROWS   = 300
FLUSH_EVERY = 20  # concat in batches to reduce DataFrame allocation overhead


class RLState:
    def __init__(self):
        self.df      = pd.DataFrame(columns=COLS)
        self.running = False
        self._buffer: list = []  # accumulate raw dicts before expensive concat

    def update(self, new_records: list):
        """Buffer incoming records and flush to the main DataFrame in batches."""
        if not new_records:
            return
        self._buffer.extend(new_records)
        if len(self._buffer) >= FLUSH_EVERY:
            self._flush()

    def _flush(self):
        """Concat the buffer into the main DataFrame, then trim to MAX_ROWS."""
        if not self._buffer:
            return
        new_df = pd.DataFrame(self._buffer, columns=COLS)
        self.df = pd.concat([self.df, new_df], ignore_index=True).iloc[-MAX_ROWS:]
        self._buffer.clear()

    def summary(self):
        """Return per-strategy mean ROI and total profit. Includes buffered records."""
        if self._buffer:
            self._flush()
        if self.df.empty:
            return None
        return (
            self.df.groupby("strategy")[["roi", "profit"]]
            .agg({"roi": "mean", "profit": "sum"})
            .reset_index()
        )

    def recent_trades(self, n: int = 10):
        """Return the n most recent trades across all strategies."""
        if self._buffer:
            self._flush()
        if self.df.empty:
            return None
        return self.df.tail(n)[["timestamp", "strategy", "roi", "profit"]].iloc[::-1]

    def totals(self):
        """Return aggregate stats: total deals, overall avg ROI, total profit, best strategy."""
        if self._buffer:
            self._flush()
        if self.df.empty:
            return None
        best = (
            self.df.groupby("strategy")["roi"].mean().idxmax()
        )
        return {
            "total_deals": len(self.df),
            "avg_roi":     round(self.df["roi"].mean(), 2),
            "total_profit": round(self.df["profit"].sum(), 2),
            "best_strategy": best,
        }
