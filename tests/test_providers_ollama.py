# tests/test_providers_ollama.py
import pytest
import respx
import httpx
from providers import providers_ollama
from providers.providers_base import ProviderError

BASE = "http://127.0.0.1:11434"
MODEL = "qwen2.5:3b-instruct"

@pytest.mark.asyncio
@respx.mock
async def test_nonstream_ok():
    # Tests a normal non-streaming Ollama request:
    # - Mocks a 200 response with "response":"hello"
    # - Verifies that generate() returns the correct string and calls the endpoint.
    provider = providers_ollama
    route = respx.post(f"{BASE}/api/generate").mock(
        return_value=httpx.Response(200, json={"response": "hello"})
    )
    out = await provider.generate("hi", model=MODEL, stream=False, options={})
    assert out == "hello"
    assert route.called

@pytest.mark.asyncio
@respx.mock
async def test_nonstream_error_field():
    # Tests non-streaming error handling:
    # - Mocks a 200 response that includes an "error" field instead of "response"
    # - Verifies that generate() raises ProviderError in this case.
    provider = providers_ollama
    respx.post(f"{BASE}/api/generate").mock(
        return_value=httpx.Response(200, json={"error": "model not loaded"})
    )
    with pytest.raises(ProviderError):
        await provider.generate("hi", model=MODEL, stream=False, options={})

@pytest.mark.asyncio
@respx.mock
async def test_stream_ok():
    # Tests a successful streaming Ollama request:
    # - Mocks multiple chunked lines coming from Ollama
    # - Verifies that generate() yields each chunk and concatenates into the final output.
    provider = providers_ollama
    # Simulate chunked lines as Ollama stream does
    chunks = [
        b'{"response":"he"}\n',
        b'{"response":"llo"}\n',
        b'{"response":""}\n',
    ]
    respx.post(f"{BASE}/api/generate").mock(
        return_value=httpx.Response(200, content=b"".join(chunks), headers={"Content-Type": "application/x-ndjson"})
    )
    gen = await provider.generate("hi", model=MODEL, stream=True, options={})
    acc = []
    async for c in gen:
        acc.append(c)
    assert "".join(acc) == "hello"

@pytest.mark.asyncio
@respx.mock
async def test_stream_error_mid():
    # Tests error handling during a stream:
    # - Mocks a stream where the second chunk contains an "error" field
    # - Verifies that generate() raises ProviderError immediately when this occurs.
    provider = providers_ollama
    chunks = [
        b'{"response":"he"}\n',
        b'{"error":"boom"}\n',
    ]
    respx.post(f"{BASE}/api/generate").mock(
        return_value=httpx.Response(200, content=b"".join(chunks), headers={"Content-Type": "application/x-ndjson"})
    )
    gen = await provider.generate("hi", model=MODEL, stream=True, options={})
    with pytest.raises(ProviderError):
        async for _ in gen:
            pass
