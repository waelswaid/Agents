# sends an async POST with httpx to OLLAMA_HOST, parses the JSON and returns the response string, 
#TODO implement stream




import httpx
from typing import Optional, Dict, Any
from .base import ProviderError
from utils.config import OLLAMA_HOST

# builds Ollama /api/generate JSON payload:
# { "model": "qwen2.5:3b-instruct", "prompt": "...", "stream": false, "options": {...} }

async def generate(prompt: str, *, model: str, stream: bool = False,
                   options: Optional[Dict[str, Any]] = None) -> str:
    if stream:
        raise ProviderError("Streaming not implemented yet in Phase 1.")
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if options:
        payload["options"] = options

    try:
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            # For non-stream generate, Ollama returns a single JSON with 'response'
            reply = data.get("response", "")
            if not isinstance(reply, str):
                raise ProviderError("Unexpected response type from Ollama.")
            return reply
    except httpx.HTTPError as e:
        raise ProviderError(f"Ollama HTTP error: {e}") from e