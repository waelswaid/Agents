import json
import httpx
from typing import Optional, Dict, Any, AsyncIterator
from app.providers.base import ProviderError, GenerateReturn
from app.core import config

def _apply_defaults(options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    opts: Dict[str, Any] = dict(options or {})
    opts.setdefault("num_ctx", config.CTX_TOKENS)
    opts.setdefault("num_predict", config.MAX_TOKENS)
    opts.setdefault("temperature", config.TEMPERATURE)
    return opts

async def _generate_streaming(payload: Dict[str, Any]) -> AsyncIterator[str]:
    timeout = httpx.Timeout(120.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", f"{config.OLLAMA_HOST}/api/generate", json=payload) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(data.get("response"), str) and data["response"]:
                    yield data["response"]
                if data.get("error"):
                    raise ProviderError(f"Ollama error: {data['error']}")

async def generate(
    prompt: str,
    *,
    model: str,
    stream: bool = False,
    options: Optional[Dict[str, Any]] = None,
) -> GenerateReturn:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": _apply_defaults(options),
    }
    try:
        if stream:
            return _generate_streaming(payload)
        timeout = httpx.Timeout(60.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{config.OLLAMA_HOST}/api/generate", json=payload)
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
