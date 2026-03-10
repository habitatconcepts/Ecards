import asyncio
import queue
import threading


class RLQueue:
    """
    Thread-safe queue bridge between async producer coroutines
    (running on a background thread's event loop) and the synchronous
    Streamlit main thread.

    Uses stdlib queue.Queue which is protected by a mutex and safe to
    put/get across threads — unlike asyncio.Queue which is NOT thread-safe.
    """

    def __init__(self):
        self.queue   = queue.Queue()   # thread-safe stdlib queue
        self.running = False
        self.tasks: list = []
        self._loop: asyncio.AbstractEventLoop | None = None

    async def launch(self, strategies, param_ref, producer):
        """Spawn one producer coroutine per strategy."""
        if self.running:
            return
        self.running = True
        self._loop = asyncio.get_event_loop()
        for s in strategies:
            task = asyncio.create_task(producer(s, self.queue, param_ref))
            self.tasks.append(task)

    def consume(self) -> list:
        """Synchronously drain all available items — safe to call from any thread."""
        items = []
        while True:
            try:
                items.append(self.queue.get_nowait())
            except queue.Empty:
                break
        return items

    def stop(self):
        """Cancel all producer tasks and reset state."""
        self.running = False
        for t in self.tasks:
            t.cancel()
        self.tasks.clear()
