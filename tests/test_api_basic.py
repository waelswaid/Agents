# tests/test_api_basic.py
import asyncio
import pytest
from typing import AsyncIterator

import app as app_module
from providers.providers_base import ProviderError

@pytest.mark.asyncio
async def test_health(client):
    # Tests the /health endpoint:
    # - Should return 200 with JSON {"status": "ok"}.
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_agents(client):
    # Tests the /agents endpoint:
    # - Should return 200 and list available agents (e.g., "general").
    r = await client.get("/agents")
    assert r.status_code == 200
    assert "general" in r.json().get("agents", [])

@pytest.mark.asyncio
async def test_chat_nonstream_ok(client, monkeypatch):
    # Tests /chat non-stream mode:
    # - Monkeypatches provider_generate to return "hello"
    # - Sends a normal POST request and verifies the JSON reply and conversation_id header.
    async def fake_generate(prompt, model, stream, options):
        assert stream is False
        return "hello"
    monkeypatch.setattr(app_module, "provider_generate", fake_generate)
    r = await client.post("/chat", json={"message": "Say hi", "agent": "general", "stream": False})
    assert r.status_code == 200
    data = r.json()
    assert data["reply"] == "hello"
    assert data["conversation_id"]

@pytest.mark.asyncio
async def test_chat_stream_ok(client, monkeypatch):
    # Tests /chat streaming mode:
    # - Monkeypatches provider_generate to yield "he" then "llo"
    # - Verifies that the streaming response concatenates correctly to "hello".
    async def fake_streamer(prompt, model, stream, options):
        assert stream is True
        async def gen() -> AsyncIterator[str]:
            yield "he"
            await asyncio.sleep(0)
            yield "llo"
        return gen()
    monkeypatch.setattr(app_module, "provider_generate", fake_streamer)
    r = await client.post("/chat", json={"message": "stream", "agent": "general", "stream": True})
    assert r.status_code == 200
    assert r.headers.get("x-conversation-id")
    body = r.text
    assert "hello" in body

@pytest.mark.asyncio
async def test_unknown_agent_400(client):
    # Tests that providing an unknown agent name results in a 400 Bad Request response.
    r = await client.post("/chat", json={"message": "hi", "agent": "nope", "stream": False})
    assert r.status_code == 400

@pytest.mark.asyncio
async def test_validation_422(client):
    # Tests FastAPI validation:
    # - Empty message field should result in a 422 Unprocessable Entity response.
    r = await client.post("/chat", json={"message": "", "agent": "general", "stream": False})
    assert r.status_code == 422
