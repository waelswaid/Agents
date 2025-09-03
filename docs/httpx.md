# 07. httpx

## Non-Streaming
```python
async with httpx.AsyncClient(timeout=60.0) as client:
    r = await client.post(url, json=payload)
    r.raise_for_status()
    data = r.json()
```

## Streaming
```python
async with httpx.AsyncClient(timeout=120.0) as client:
    async with client.stream("POST", url, json=payload) as r:
        r.raise_for_status()
        async for line in r.aiter_lines():
            ...
```

### Tips
- Prefer a **single client per request** (simple) or a **module-level client** (perf) if single-worker.
- Always `raise_for_status()`, and catch `httpx.HTTPError` to wrap in `ProviderError`.
- For NDJSON, process per-line; guard against empty lines.
