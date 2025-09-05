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
            err = data.get("error")
            if isinstance(err, str) and err:
                raise ProviderError(f"Ollama error: {err}")
            reply = data.get("response", "")
            if not isinstance(reply, str):
                raise ProviderError("Unexpected response type from Ollama.")
            return reply
    except httpx.HTTPError as e:
        raise ProviderError(f"Ollama HTTP error: {e}") from e