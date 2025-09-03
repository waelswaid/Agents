# 17. Decisions (ADR-lite)

## 0001 — Provider Contract Returns str *or* AsyncIterator[str]
- Options: separate methods for stream vs non-stream | union return type
- Chosen: union return type
- Why: keep route logic unified; simpler provider plugins
- Tradeoffs: need clear type checks at call site

## 0002 — Streaming Format = Chunked Text
- Options: Chunked | SSE | WebSocket
- Chosen: Chunked
- Why: simplest universal solution; works with curl/fetch
- Tradeoffs: no event typing; add SSE later for browsers

## 0003 — Short-Term Memory = In-Memory with TTL + LRU
- Options: per-process memory | Redis | SQLite
- Chosen: in-memory (Phase 2)
- Why: simplest on Pi; easy swap-out later
- Tradeoffs: not shared across workers; use Redis/DB in Phase 4
