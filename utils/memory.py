from __future__ import annotations
from collections import deque
from typing import Deque, Dict, List, TypedDict
import asyncio
import time

class Turn(TypedDict):
    role: str         # "user" | "assistant"
    content: str
    ts: float

class MemoryStore:
    """
    Very small, Pi-friendly in-memory conversation store.
    - Per-conversation deque capped by max_turns
    - Optional TTL eviction
    - LRU cap on total conversations
    """
    def __init__(
        self,
        *,
        max_turns: int = 8,
        ttl_seconds: int = 60 * 60,
        max_conversations: int = 500,
    ) -> None:
        self._store: Dict[str, Deque[Turn]] = {}
        self._last: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._max_turns = max(1, max_turns)
        self._ttl = max(0, ttl_seconds)
        self._max_convos = max(1, max_conversations)

    async def get(self, convo_id: str) -> List[Turn]:
        await self._maybe_prune(convo_id)
        dq = self._store.get(convo_id)
        return list(dq) if dq else []

    async def append(self, convo_id: str, role: str, content: str) -> None:
        now = time.time()
        async with self._lock:
            dq = self._store.get(convo_id)
            if dq is None:
                dq = deque(maxlen=self._max_turns)
                self._store[convo_id] = dq
            dq.append({"role": role, "content": content, "ts": now})
            self._last[convo_id] = now
            # LRU eviction if we exceed the global limit
            if len(self._store) > self._max_convos:
                oldest = min(self._last.items(), key=lambda kv: kv[1])[0]
                self._store.pop(oldest, None)
                self._last.pop(oldest, None)

    async def _maybe_prune(self, convo_id: str) -> None:
        if self._ttl <= 0:
            return
        now = time.time()
        ts = self._last.get(convo_id)
        if ts and (now - ts) > self._ttl:
            async with self._lock:
                self._store.pop(convo_id, None)
                self._last.pop(convo_id, None)