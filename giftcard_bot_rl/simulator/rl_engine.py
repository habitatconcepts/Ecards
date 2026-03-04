import asyncio, random
from datetime import datetime

async def simulate_strategy(name, queue, param_ref):
    """Continuously yield trades using live-updating parameters from param_ref dict."""
    deal_id = 0
    while True:
        await asyncio.sleep(max(0.3, 3.0 - param_ref[name]["speed"]))
        deal_id += 1
        fv = random.choice([50, 100, 150, 200])
        config = param_ref[name]
        base_roi = random.uniform(*config["roi_target"])
        volatility = config["volatility"]
        roi = max(0, min(random.gauss(base_roi, 10 * volatility), 80))
        profit = round(fv * roi / 100, 2)
        await queue.put({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "strategy": name,
            "deal_id": deal_id,
            "roi": roi,
            "profit": profit
        })
