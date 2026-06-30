import asyncio
from collections import defaultdict


class AlbumBuffer:

    def __init__(self):
        self.buffer = {}
        self.groups = defaultdict(set)
        self.tasks = {}

    def add(self, key, msg):
        self.buffer[msg.message_id] = msg
        self.groups[key].add(msg.message_id)

    def cancel(self, key):
        task = self.tasks.get(key)
        if task:
            task.cancel()

    def set_task(self, key, task):
        self.tasks[key] = task

    def pop_group(self, key):
        ids = list(self.groups.pop(key, set()))
        msgs = [self.buffer.pop(i) for i in ids if i in self.buffer]
        return msgs