# 05. Providers & Registry

## Contract
```python
from typing import AsyncIterator, Union, Dict, Any

GenerateReturn = Union[str, AsyncIterator[str]]

async def generate(
    prompt: str,
    model: str,
    host: str,
    stream: bool,
    options: Dict[str, Any]
) -> GenerateReturn:
    ...
```

- Return **string** for non-stream; **async iterator** of string chunks for stream.
- This keeps `app.py` agnostic to the backend (Ollama, OpenAI, etc.).

## Adding a New Provider
1. Create `providers/<name>.py` implementing `generate(...)`.
2. Map config → provider options (ctx, max tokens, temperature, etc.).
3. Extend provider switch/registry in `app.py` (or a registry dict).

## Error Surface
- Wrap provider/HTTP errors in `ProviderError(message)`.
- Route maps `ProviderError` → `HTTP 502` with `{"detail": message}`.
