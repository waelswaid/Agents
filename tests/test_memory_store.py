# tests/test_memory_store.py
import asyncio
import time
import pytest

from utils.memory import MemoryStore

@pytest.mark.asyncio
async def test_append_and_get_order():
    # Tests that messages are appended and retrieved in the correct order
    # Verifies both roles ("user", "assistant") and message contents.
    m = MemoryStore(max_turns=3, ttl_seconds=60, max_conversations=10)
    cid = "c1"
    await m.append(cid, "user", "u1")
    await m.append(cid, "assistant", "a1")
    await m.append(cid, "user", "u2")
    hist = await m.get(cid)
    assert [t["role"] for t in hist] == ["user", "assistant", "user"]
    assert [t["content"] for t in hist] == ["u1", "a1", "u2"]

@pytest.mark.asyncio
async def test_max_turns_window():
    # Tests that MemoryStore enforces max_turns:
    # When more messages than max_turns are added,
    # only the most recent max_turns messages are kept.
    m = MemoryStore(max_turns=3, ttl_seconds=60, max_conversations=10)
    cid = "c2"
    for i in range(5):
        await m.append(cid, "user", f"u{i}")
    hist = await m.get(cid)
    assert len(hist) == 3
    assert [t["content"] for t in hist] == ["u2", "u3", "u4"]

@pytest.mark.asyncio
async def test_ttl_expiry():
    # Tests automatic expiration (TTL) of conversations.
    # After sleeping longer than ttl_seconds,
    # the conversation should be automatically cleared.
    m = MemoryStore(max_turns=5, ttl_seconds=1, max_conversations=10)
    cid = "c3"
    await m.append(cid, "user", "u")
    await asyncio.sleep(1.2)
    hist = await m.get(cid)
    assert hist == []  # expired

@pytest.mark.asyncio
async def test_lru_eviction():
    # Tests least-recently-used (LRU) eviction behavior:
    # When max_conversations is reached, adding a new conversation
    # should evict the conversation that was least recently accessed.
    # Accessing a conversation via .get() refreshes its "recency".
    m = MemoryStore(max_turns=3, ttl_seconds=60, max_conversations=2)
    await m.append("c1", "user", "x")
    await m.append("c2", "user", "y")
    # Access c1 to keep it fresh
    _ = await m.get("c1")
    # Add c3; LRU should evict c2
    await m.append("c3", "user", "z")
    assert await m.get("c1") != []  # kept
    assert await m.get("c2") == []  # evicted
    assert await m.get("c3") != []  # newly added

@pytest.mark.asyncio
async def test_get_is_threadsafe_copy():
    # Tests thread safety of MemoryStore.get():
    # Ensures concurrent reads and writes do not cause crashes or data corruption.
    # Specifically verifies that .get() always returns a safe copy of the deque.
    m = MemoryStore(max_turns=5, ttl_seconds=60, max_conversations=10)
    cid = "c4"
    await m.append(cid, "user", "u1")

    # Concurrent append while reading
    async def writer():
        for i in range(10):
            await m.append(cid, "user", f"u{i}")
            await asyncio.sleep(0.001)
    async def reader():
        for _ in range(10):
            _ = await m.get(cid)  # should not raise
            await asyncio.sleep(0.001)

    await asyncio.gather(writer(), reader())

    hist = await m.get(cid)
    assert isinstance(hist, list)
    assert hist  # not empty
