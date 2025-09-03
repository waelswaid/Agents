# 10. Conversation Memory (TTL + LRU)

## Data Structure
- `Dict[str, Deque[Turn]]`, bounded by `MEMORY_MAX_TURNS`.
- `Turn = {role: "user"|"assistant", content: str, ts: float}`.
- `_last: Dict[convo_id, last_touch_ts]` for TTL & LRU.

## Behavior
- `get(id)`: prune by TTL if idle; return a **copy** of the deque.
- `append(id, role, content)`: add turn, update `_last`, enforce global LRU by evicting oldest when over `MEMORY_MAX_CONVERSATIONS`.
- Streaming: append **user** and **concatenated assistant** in `finally:` once stream completes (or disconnect) to avoid losing partial outputs.

## Concurrency
- Single `asyncio.Lock` for writes/evictions; reads are mostly lock-free.

## Future
- If running multiple workers, swap to **Redis** or **SQLite** (same interface) to share memory across processes.
