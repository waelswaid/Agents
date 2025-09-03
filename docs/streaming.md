# Streaming — Phase 2


This guide explains **how streaming works** in your FastAPI agent server, in three layers:

1. **HTTP streaming basics** — how chunked responses differ from non-stream.
2. **Server architecture** — how `app.py` produces a streaming response.
3. **Provider architecture** — how `providers/ollama.py` pulls NDJSON from Ollama and yields chunks.

It also covers **client tips**, **operational gotchas**, and **how to extend** (e.g., SSE).

## 1) HTTP Streaming Basics (Chunked Transfer)


When `stream=true`, the server **does not** wait for the full model reply. Instead it sends the answer in **small chunks** as soon as they are produced.

- **Non-stream**: one HTTP response body sent at the end.
- **Stream**: many small pieces (bytes) sent over the same HTTP response, terminated when the model is done.

Benefits:
- **Fast first byte** → better perceived latency (critical on Pi).
- **Early stop** → clients can cancel when they've seen enough.
- **Resilience** → even partial output is useful if something fails later.

In FastAPI, we implement this with **`StreamingResponse`** and an **async generator** that `yield`s bytes as they arrive.

## 2) Streaming in `app.py` — The Endpoint Flow


A simplified version of the streaming branch in `app.py` looks like this:

```python
gen = await provider_generate(prompt, model=config.OLLAMA_MODEL_GENERAL, stream=True, options=options)

async def streamer():
    acc = []
    try:
        async for chunk in gen:
            acc.append(chunk)
            if await request.is_disconnected():
                break
            yield chunk.encode("utf-8")
    finally:
        if config.ENABLE_MEMORY:
            await _memory.append(convo_id, "user", req.message)
            if acc:
                await _memory.append(convo_id, "assistant", "".join(acc))

headers = {"X-Conversation-Id": convo_id}
return StreamingResponse(streamer(), media_type="text/plain; charset=utf-8", headers=headers)
```

**Line-by-line:**

1. Call provider with `stream=True` → returns an async iterator of text chunks.
2. Define `streamer()` generator:
   - Iterate over provider chunks.
   - Yield them to the client immediately.
   - Stop if the client disconnects.
3. In `finally:` → update memory with user input and assistant’s concatenated reply (even partial).
4. Wrap generator in `StreamingResponse`, attach `X-Conversation-Id` header.

This produces a **live token stream** instead of one big JSON.

## 3) Provider Side — `providers/ollama.py`


Ollama streams NDJSON (newline-delimited JSON). Each line contains part of the response.

```python
async def _generate_streaming(payload: Dict[str, Any]) -> AsyncIterator[str]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
        async with client.stream("POST", f"{config.OLLAMA_HOST}/api/generate", json=payload) as r:
            async for line in r.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if "error" in data:
                    raise ProviderError(data["error"])
                if "response" in data:
                    yield data["response"]
```

- `client.stream(...)`: opens a streaming HTTP request to Ollama.
- `r.aiter_lines()`: yields each NDJSON line as soon as available.
- Parse JSON, extract `"response"`, and yield it upward.
- If an error is present, raise `ProviderError` to abort cleanly.

### Unified `generate(...)` contract


```python
async def generate(prompt: str, *, model: str, stream: bool = False, options=None):
    payload = {...}
    if stream:
        return _generate_streaming(payload)
    else:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            r = await client.post(f"{config.OLLAMA_HOST}/api/generate", json=payload)
            data = r.json()
            if "error" in data:
                raise ProviderError(data["error"])
            return data["response"]
```

- Non-stream returns one full string.
- Stream returns the async iterator from `_generate_streaming`.

This unified interface lets `app.py` stay simple.

## 4) Client Usage Tips


**Capture headers + body:**
```bash
curl -N -i -s -X POST http://127.0.0.1:8000/chat   -H "Content-Type: application/json"   -d '{"message":"count to five","agent":"general","stream":true}'
```

Look for:
```
x-conversation-id: <uuid>
```

**Reuse conversation:**
```bash
curl -N -s -X POST http://127.0.0.1:8000/chat   -H "Content-Type: application/json"   -d '{"message":"continue","agent":"general","stream":true,"conversation_id":"<uuid>"}'
```

## 5) Operational Gotchas


1. **Reverse proxies may buffer** → disable buffering in Nginx/Caddy to preserve streaming feel.

2. **Timeouts** → ensure both FastAPI and proxy allow long-lived responses.

3. **Scaling** → Memory is per-process; use Redis/DB store when scaling horizontally.

4. **Metrics** → Track latency-to-first-token and total duration.


## 6) SSE vs Plain Text


Current design streams raw text chunks (`text/plain`).  
For browser-native streaming, you can switch to **SSE (Server-Sent Events)**:

- Change `media_type` to `text/event-stream`.
- Yield events like: `yield f"data: {chunk}\n\n".encode()`.
- Client can use `EventSource` API in JavaScript.

This adds framing but improves browser support.

## 7) Why This Works Well on Pi


- Very lightweight: no websockets, just HTTP chunking.

- Async ensures efficient use of limited cores.

- Backpressure built-in (only read as client consumes).

- Supports partial replies if interrupted.

