import asyncio
import random
from datetime import datetime


async def simulate_strategy(name, sync_queue, param_ref):
    """
    Async producer that runs on the background thread's event loop.
    Writes results into a stdlib queue.Queue (thread-safe) so the
    Streamlit main thread can drain it synchronously via consume().
    """
    deal_id = 0
    while True:
        await asyncio.sleep(max(0.3, 3.0 - param_ref[name]["speed"]))
        deal_id += 1
        fv     = random.choice([50, 100, 150, 200])
        config = param_ref[name]
        base_roi   = random.uniform(*config["roi_target"])
        volatility = config["volatility"]
        roi    = max(0.0, min(random.gauss(base_roi, 10 * volatility), 80.0))
        profit = round(fv * roi / 100, 2)
        # put_nowait is safe: queue.Queue has no maxsize by default
        sync_queue.put_nowait({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "strategy":  name,
            "deal_id":   deal_id,
            "roi":       roi,
            "profit":    profit,
        })
