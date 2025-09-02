# sends an async POST with httpx to OLLAMA_HOST, parses the JSON and returns the response string, 
#TODO implement stream




import httpx
from typing import Optional, Dict, Any
from .base import ProviderError
from utils.config import OLLAMA_HOST

# builds Ollama /api/generate JSON payload:
# { "model": "qwen2.5:3b-instruct", "prompt": "...", "stream": false, "options": {...} }




"""
defines an async function (can use await inside).
options parameter: optional generation settings (like temperature, max_tokens, etc).
the '->str' at the end means it's expected to return a string.
"""
async def generate(prompt: str, *, model: str, stream: bool = False,
                   options: Optional[Dict[str, Any]] = None) -> str:
    if stream:
        raise ProviderError("Streaming not implemented yet in Phase 1.")
    # builds a json payload to send to ollama
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    # if the caller provides extra generation controls, add them under the 'options' key
    if options:
        payload["options"] = options

    try:
        timeout = httpx.Timeout(30.0, connect=10.0) # wraps netwrok call with try/except, 10s to establish a connection, 30s total for the request,
        #prevents the api from hanging forever if ollama is slow or unreachable.


        # create an async http client using httpx
        async with httpx.AsyncClient(timeout=timeout) as client:
            # sends POST request to ollama with the JSON payload
            r = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
            # if ollama returns a non-2xx status (like 400 or 500), raise an httpx.HTTPStatusError
            r.raise_for_status()
            # parses the HTTP response body as JSON into a python dict
            data = r.json()
            # For non-stream generate, Ollama returns a single JSON with 'response'
            # extracts the text reply from the 'response' field of ollama's JSON
            reply = data.get("response", "")
            # defensive check ensures reply is a string
            if not isinstance(reply, str):
                raise ProviderError("Unexpected response type from Ollama.")
            return reply
    except httpx.HTTPError as e:
        raise ProviderError(f"Ollama HTTP error: {e}") from e