import pandas as pd

class RLState:
    def __init__(self):
        self.df = pd.DataFrame(columns=["timestamp", "strategy", "deal_id", "roi", "profit"])
        self.running = False

    def update(self, new_records):
        if new_records:
            self.df = pd.concat([self.df, pd.DataFrame(new_records)], ignore_index=True)
            self.df = self.df.tail(300)

    def summary(self):
        if self.df.empty:
            return None
        return (
            self.df.groupby("strategy")[["roi", "profit"]]
            .agg({"roi": "mean", "profit": "sum"})
            .reset_index()
        )
