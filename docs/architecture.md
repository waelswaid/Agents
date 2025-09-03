# 01. Architecture

## High-Level Flow
```
Client → /chat (FastAPI)
  ├─ Pydantic validates request (ChatRequest)
  ├─ Load system prompt & recent history (if memory enabled)
  ├─ Build final prompt (system + history + user)
  ├─ Provider.generate(..., stream=bool)
  │    ├─ Non-stream: returns final string
  │    └─ Stream: async iterator of token chunks
  ├─ Update memory (non-stream immediately; stream on finalize)
  └─ Respond (JSON or chunked text) + headers (X-Conversation-Id)
```

## Modules
- `app.py` — app creation, endpoints, streaming, error mapping, memory integration.
- `agents/base.py` — prompt composition from system + history + user.
- `agents/general.py` — loads `prompts/general_system.txt`.
- `providers/base.py` — `ProviderError`, `GenerateReturn` contract.
- `providers/ollama.py` — NDJSON streaming from Ollama; non-stream fallback.
- `utils/config.py` — env vars → options mapping (`num_ctx`, `num_predict`, `temperature`).
- `utils/memory.py` — TTL + LRU-limited in-memory store.

## Sequence (Streaming)
```
Client          FastAPI            Provider (Ollama)            Memory
  | POST /chat    |                         |                     |
  | stream=true   | validate → build prompt |                     |
  |-------------->|                         |                     |
  |               |   call generate(stream) |                     |
  |               |------------------------>|                     |
  |               |   iterate NDJSON lines  |                     |
  |               |<------------------------| "chunk"             |
  |  receive chunk|                         |                     |
  |  receive chunk|                         |                     |
  |  ...          |                         |                     |
  | (disconnect?) | detect & stop           |                     |
  |               | finally: append turns   |-------------------->|
  |               | set X-Conversation-Id   |                     |
```

Design choices and tradeoffs are captured in [decisions.md](decisions.md).
