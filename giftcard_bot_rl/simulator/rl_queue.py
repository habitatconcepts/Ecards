import asyncio
from asyncio import Queue

class RLQueue:
    def __init__(self):
        self.queue = Queue()
        self.running = False
        self.tasks = []

    async def launch(self, strategies, param_ref, producer):
        if self.running:
            return
        self.running = True
        for s in strategies:
            task = asyncio.create_task(producer(s, self.queue, param_ref))
            self.tasks.append(task)

    async def consume(self):
        items = []
        while not self.queue.empty():
            items.append(await self.queue.get())
        return items

    def stop(self):
        self.running = False
        for t in self.tasks:
            t.cancel()
        self.tasks.clear()
