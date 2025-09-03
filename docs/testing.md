# 12. Testing Strategy & Examples

## Tools
- `pytest`
- `httpx.ASGITransport` to call FastAPI in-process

## Example: streaming smoke test
```python
import pytest, httpx
from app import app

@pytest.mark.anyio
async def test_streaming_first_tokens():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream("POST", "/chat", json={"message":"hi","agent":"general","stream":True}) as r:
            assert r.status_code == 200
            chunks = []
            async for line in r.aiter_lines():
                if line:
                    chunks.append(line)
                if len(chunks) >= 2:
                    break
    assert len(chunks) >= 1
```

## Example: memory LRU/TTL tests
- Create N+1 conversations → expect oldest evicted.
- Append, advance time, call `get` after TTL → expect purge.

## Non-stream tests
- Valid request → JSON response matches `ChatResponse`.
- Provider error → 502 with detail.
- Validation errors → 422 with `detail` list.
