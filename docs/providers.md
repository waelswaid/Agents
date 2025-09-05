# Providers Module Documentation
---
## providers/providers_base.py

### Overview
Defines the base provider contract and error handling for LLM interactions.

### Classes

#### `ProviderError`
**Purpose:** Custom exception for provider-specific errors.

**Attributes:**
- `message` (str): Error description
- `status_code` (int): HTTP status code (defaults to 502)

**Example:**
```python
raise ProviderError("Failed to connect to LLM", status_code=503)
```

### Types

#### `GenerateReturn`
**Purpose:** Type alias for provider response formats.
```python
GenerateReturn = Union[str, AsyncIterator[str]]
```
- `str`: Complete response for non-streaming
- `AsyncIterator[str]`: Token stream for streaming

## Full Code

- providers/providers_base.py
```python
# let's us swap/add providers later without touching endpoint logic (local/openai/deepseek...)
# declares the abstract provider contract (generate(...)) that all providers must implement

from typing import Optional, Dict, Any, AsyncIterator, Union


# defines a provideerror for consistent error handling at the app layer so the api can distinguish provider faults from user errors
class ProviderError(Exception):
    pass


# When stream=False -> returns a single string
# When stream=True  -> returns an async iterator of text chunks
GenerateReturn = Union[str, AsyncIterator[str]]

async def generate(
    prompt: str,
    *,
    model: str,
    stream: bool = False,
    options: Optional[Dict[str, Any]] = None,
) -> GenerateReturn:
    """Abstract provider interface."""
    raise NotImplementedError  # implemented by providers/<name>.py
```

---

## providers/providers_ollama.py

### Overview
Implements the Ollama API provider with streaming and non-streaming support.

### Functions

#### `_apply_defaults(options: Optional[Dict[str, Any]]) -> Dict[str, Any]`
**Purpose:** Applies default configuration values to Ollama request options.

**Parameters:**
- `options` (Optional[Dict[str, Any]]): Custom options

**Returns:**
- Dictionary with complete Ollama configuration

**Example:**
```python
opts = _apply_defaults({"temperature": 0.7})
# Returns: {"temperature": 0.7, "num_ctx": 4096, "num_predict": 1024}
```

#### `_generate_streaming(payload: Dict[str, Any]) -> AsyncIterator[str]`
**Purpose:** Handles streaming responses from Ollama API.

**Parameters:**
- `payload` (Dict[str, Any]): Request body for Ollama

**Returns:**
- `AsyncIterator[str]`: Stream of text chunks

**Example:**
```python
async for chunk in _generate_streaming({"prompt": "Hello", "model": "qwen:3b"}):
    print(chunk)
```

#### `generate(prompt: str, *, model: str, stream: bool = False, options: Optional[Dict[str, Any]] = None) -> GenerateReturn`
**Purpose:** Main generation function, wraps Ollama's /api/generate endpoint.

**Parameters:**
- `prompt` (str): Input text
- `model` (str): Model identifier
- `stream` (bool): Enable streaming mode
- `options` (Optional[Dict[str, Any]]): Custom configuration

**Returns:**
- `str` or `AsyncIterator[str]` depending on stream mode

**Example:**
```python
# Non-streaming
response = await generate("Hello!", model="qwen:3b")

# Streaming
async for chunk in await generate("Hello!", model="qwen:3b", stream=True):
    print(chunk)
```

## Full Code

- providers/providers_ollama.py
```python
import json
import httpx
from typing import Optional, Dict, Any, AsyncIterator, Union
from providers.providers_base import ProviderError, GenerateReturn
from utils.config import (
    OLLAMA_HOST,
    CTX_TOKENS,
    MAX_TOKENS,
    TEMPERATURE,
)

def _apply_defaults(options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    opts: Dict[str, Any] = dict(options or {})
    # map server caps to Ollama options if caller didn’t set them
    opts.setdefault("num_ctx", CTX_TOKENS)
    opts.setdefault("num_predict", MAX_TOKENS)
    opts.setdefault("temperature", TEMPERATURE)
    return opts

async def _generate_streaming(payload: Dict[str, Any]) -> AsyncIterator[str]:
    timeout = httpx.Timeout(120.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", f"{OLLAMA_HOST}/api/generate", json=payload) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    # ignore malformed lines
                    continue
                # normal chunks carry 'response'; a final line has 'done': true
                chunk = data.get("response")
                if isinstance(chunk, str) and chunk:
                    yield chunk
                # if the server reports an error mid-stream, stop early
                if data.get("error"):
                    raise ProviderError(f"Ollama error: {data['error']}")

async def generate(
    prompt: str,
    *,
    model: str,
    stream: bool = False,
    options: Optional[Dict[str, Any]] = None,
) -> GenerateReturn:
    """
    Ollama /api/generate wrapper.
    - stream=False: returns full string
    - stream=True : returns async iterator of text chunks
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": _apply_defaults(options),
    }
    try:
        if stream:
            return _generate_streaming(payload)
        # non-stream path
        timeout = httpx.Timeout(60.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            reply = data.get("response", "")
            if not isinstance(reply, str):
                raise ProviderError("Unexpected response type from Ollama.")
            return reply
    except httpx.HTTPError as e:
        raise ProviderError(f"Ollama HTTP error: {e}") from e
```