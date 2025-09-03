# Pi FastAPI Agent Server — Phase 2 Implementation Report
**Streaming tokens + Short conversation memory**  


## SCOPE & GOAL
This document captures every change and addition implemented to move the Pi FastAPI Agent Server from Phase 1 (single agent, non-stream) to Phase 2 with: (1) streaming token responses and (2) short conversation memory. It explains the WHY and HOW, file-by-file, including API behavior, data structures, and practical testing steps.

## FINAL BEHAVIOR SUMMARY (WHAT WORKS NOW)
- `/health` — liveness check returns `{ "status":"ok" }`.
- `/agents` — returns `{ "agents":["general"] }`.
- `/chat` — non-stream path: returns typed JSON with `{reply, conversation_id, model?, provider?}`.
- `/chat` — stream path: returns a chunked text stream of tokens as they are generated.
- Conversation memory: when ENABLE_MEMORY=true, the server keeps a short tail of turns per conversation_id and injects them into the prompt.
- Conversation ID is also returned for streaming in the response header `X-Conversation-Id`.

## HIGH-LEVEL CHANGES (DIFF OVERVIEW)
1. Added in-memory conversation store (`utils/memory.py`) with FIFO caps, TTL, global LRU limit.
2. Extended provider contract to support streaming async iterator.
3. Implemented streaming for Ollama provider (NDJSON lines → text chunks).
4. Included history into prompts (`agents/base.py`).
5. Updated `/chat` to accept `conversation_id`, return stream/non-stream properly, attach headers, and update memory.
6. Expanded config (`utils/config.py`) with memory flags.
7. Made `model`/`provider` optional in ChatResponse to avoid validation errors.

## FILE-BY-FILE DEEP DIVE
### utils/config.py
- New env vars: ENABLE_MEMORY, MEMORY_MAX_TURNS, MEMORY_TTL_MIN, MEMORY_MAX_CONVERSATIONS.
- Caps (CTX_TOKENS, MAX_TOKENS, TEMPERATURE) mapped to provider options.

### utils/memory.py
- Dict of deques keyed by conversation_id.
- Deque tail ensures max turns.
- TTL pruning + global LRU eviction.

### agents/base.py
- `_render_history` renders past turns into `<user>` and `<assistant>` blocks.
- `build_prompt` = system + history + new user.

### providers/base.py
- Contract updated: returns `str` (non-stream) or `AsyncIterator[str]` (stream).

### providers/ollama.py
- Implements streaming: parse NDJSON, yield `response` tokens.
- Non-stream: single POST returns `response`.

### app.py
- `ChatRequest`: adds `conversation_id`, `stream`.
- `ChatResponse`: includes reply, conversation_id, model?, provider?.
- Non-stream: full reply JSON, append to memory.
- Stream: async generator yields chunks, updates memory in `finally`, attaches header.

## API CONTRACT — Quick Reference
- `GET /health` → `{ "status":"ok" }`
- `GET /agents` → `{ "agents":["general"] }`
- `POST /chat` (non-stream):
```json
{"message":"hi","agent":"general","stream":false}
```
Response:
```json
{"reply":"...","conversation_id":"<id>","model":null,"provider":null}
```
- `POST /chat` (stream):
```json
{"message":"hi","agent":"general","stream":true}
```
Response: chunked text stream, header `X-Conversation-Id`.

## TESTING & USAGE — CURLs
- Non-stream:
```bash
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"say hello","agent":"general","stream":false}'
```
- Stream (show headers):
```bash
curl -N -i -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"count to five","agent":"general","stream":true}'
```
- Reuse conversation:
```bash
curl -N -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"continue","agent":"general","stream":true,"conversation_id":"<id>"}'
```

## WHY THESE DESIGN CHOICES (PI-FOCUSED)
- Async: maximize concurrency.
- Short memory with caps: predictable RAM and tokens.
- Simple prompt format: efficient.
- Streaming: better UX on Pi.
- Env-driven config: portable between Pi and cloud.

## KNOWN LIMITATIONS & NEXT STEPS
- Memory is per-process → for multi-instance, use Redis/SQLite.
- No rate limiting, CORS, or API key yet (Phase 5).
- Only Ollama implemented; add `providers/openai.py` for cloud.
- Logging not yet structured.
- SSE not implemented (optional).

## APPENDIX — Example .env
```ini
PROVIDER=ollama
OLLAMA_MODEL_GENERAL=qwen2.5:3b-instruct
OLLAMA_HOST=http://127.0.0.1:11434
CTX_TOKENS=2048
MAX_TOKENS=200
TEMPERATURE=0.7
ENABLE_MEMORY=true
MEMORY_MAX_TURNS=8
MEMORY_TTL_MIN=60
MEMORY_MAX_CONVERSATIONS=500
```
