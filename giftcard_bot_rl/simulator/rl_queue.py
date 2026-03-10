import asyncio
from asyncio import Queue, QueueEmpty


class RLQueue:
    def __init__(self):
        self.queue   = Queue()
        self.running = False
        self.tasks: list = []

    async def launch(self, strategies, param_ref, producer):
        """Spawn one producer task per strategy. No-op if already running."""
        if self.running:
            return
        self.running = True
        for s in strategies:
            task = asyncio.create_task(producer(s, self.queue, param_ref))
            self.tasks.append(task)

    async def consume(self) -> list:
        """Drain all currently available items without blocking.

        Uses get_nowait() to avoid async overhead from awaiting get() in a
        loop that already confirms the queue is non-empty.
        """
        items = []
        while True:
            try:
                items.append(self.queue.get_nowait())
            except QueueEmpty:
                break
        return items

    def stop(self):
        """Cancel all producer tasks and reset state."""
        self.running = False
        for t in self.tasks:
            t.cancel()
        self.tasks.clear()
