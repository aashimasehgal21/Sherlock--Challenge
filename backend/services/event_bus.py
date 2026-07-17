"""
backend/services/event_bus.py
--------------------------------
A tiny in-memory pub/sub event bus, scoped per meeting_id.

This is what makes the system EVENT-DRIVEN instead of polling: when a
new event comes in (participant joined, new transcript line, speaking
update), we recompute the prediction ONCE and PUSH it to every
subscriber (e.g. a WebSocket client) - the client never has to ask
"anything new?" on a timer.

Deliberately simple (asyncio.Queue per subscriber) - no external
message broker needed for a prototype. For real production scale
across multiple server instances, swap this for Redis Pub/Sub or a
proper message queue (documented in README as a scaling note) - the
publish()/subscribe() interface would stay identical.
"""

import asyncio
from collections import defaultdict
from typing import Any, Dict, List


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, meeting_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[meeting_id].append(queue)
        return queue

    def unsubscribe(self, meeting_id: str, queue: asyncio.Queue) -> None:
        if queue in self._subscribers.get(meeting_id, []):
            self._subscribers[meeting_id].remove(queue)

    async def publish(self, meeting_id: str, message: Dict[str, Any]) -> None:
        for queue in self._subscribers.get(meeting_id, []):
            await queue.put(message)


# One shared instance for the whole app (simple singleton - fine for a
# single-process prototype; see docstring above for scaling past that)
event_bus = EventBus()
