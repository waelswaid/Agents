# 06. Ollama Provider Details

## Non-Streaming
- Endpoint: `POST {OLLAMA_HOST}/api/generate`
- Payload (example):
```json
{
  "model": "qwen2.5:3b-instruct",
  "prompt": "<system>...",
  "stream": false,
  "options": {
    "num_ctx": 2048,
    "num_predict": 200,
    "temperature": 0.7
  }
}
```
- Response:
```json
{"model":"...","created_at":"...","response":"...","done":true}
```

## Streaming (NDJSON)
- Same endpoint with `"stream": true`.
- Each line is JSON; when `"response"` appears, append to output.
- If a line includes `"error"`, raise `ProviderError` to abort.

**Pseudo-code:**
```python
async with client.stream("POST", url, json=payload) as r:
    async for line in r.aiter_lines():
        data = json.loads(line)
        if "error" in data:
            raise ProviderError(data["error"])
        if "response" in data:
            yield data["response"]
```

**Timeouts:**
- Use larger totals for streams (e.g., 120s) vs non-stream (60s).
