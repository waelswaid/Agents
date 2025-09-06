# Context window = system prompt + conversation history + user message

from __future__ import annotations
from collections import deque
from typing import Deque, Dict, List, TypedDict
import asyncio
import time

class Turn(TypedDict): # each turn is a dict
    role: str
    content: str
    ts: float

class MemoryStore:
    def __init__(self, *, max_turns: int = 8, ttl_seconds: int = 3600, max_conversations: int = 500) -> None:
        """
        self._store: Holds the actual conversation history for each active conversation.
        Maps conversation_id (str) → deque of turns Deque[Turn]
        self._last: Tracks the last activity timestamp for each conversation.
        Maps conversation_id (str) → last activity timestamp (float)
        """
        self._store: Dict[str, Deque[Turn]] = {}
        self._last: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._max_turns = max(1, max_turns) # at least 1 turn per conversation
        self._ttl = max(0, ttl_seconds) # 0 means no TTL
        self._max_convos = max(1, max_conversations)


    """
    When the service needs to build a prompt:
    1. It calls memory.get(convo_id) to retrieve the list of turns for that conversation.
    2. The get method first checks if the conversation has expired based on TTL and prunes it if necessary.
    3. It then returns the list of turns (role, content, timestamp) for that conversation.
    4. The service uses this list to construct the prompt.
    5. If the conversation does not exist or has expired, an empty list is returned.
    6. The service can then handle this case appropriately (e.g., start a new conversation).
    """
    async def get(self, convo_id: str) -> List[Turn]:
        await self._maybe_prune(convo_id)
        async with self._lock:
            dq = self._store.get(convo_id)
            if not dq:
                return []
            self._last[convo_id] = time.time()
            return list(dq)

    # when a new message is added to a conversation, we append it to the deque inside self._store
    # we also update the last activity timestamp in self._last
    async def append(self, convo_id: str, role: str, content: str) -> None:
        now = time.time()
        async with self._lock:
            dq = self._store.get(convo_id)
            if dq is None:
                dq = deque(maxlen=self._max_turns)
                self._store[convo_id] = dq
            dq.append({"role": role, "content": content, "ts": now})
            self._last[convo_id] = now
            if len(self._store) > self._max_convos:
                oldest = min(self._last.items(), key=lambda kv: kv[1])[0]
                self._store.pop(oldest, None)
                self._last.pop(oldest, None)
    
    # check if a conversation has expired based on TTL and prune it if necessary
    # if ttl is 0 or negative, we skip pruning
    async def _maybe_prune(self, convo_id: str) -> None:
        if self._ttl <= 0:
            return
        now = time.time()
        ts = self._last.get(convo_id)
        if ts and (now - ts) > self._ttl:
            async with self._lock:
                self._store.pop(convo_id, None)
                self._last.pop(convo_id, None)
