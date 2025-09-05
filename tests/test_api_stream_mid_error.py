# tests/test_api_stream_mid_error.py
import asyncio
import pytest
from typing import AsyncIterator
import app as app_module

@pytest.mark.asyncio
async def test_stream_mid_exception_is_logged_and_partial_returned(client, monkeypatch, caplog_info):
    # Tests what happens if provider_generate raises an error mid-stream:
    # - The first chunk is yielded successfully
    # - The error is logged using logger.exception()
    # - The server still returns 200 and includes partial output instead of crashing.

    # Fake generator: yields one chunk, then raises
    async def fake_streamer(prompt, model, stream, options):
        async def gen() -> AsyncIterator[str]:
            yield "partial "
            await asyncio.sleep(0)
            raise RuntimeError("network dropped")
        return gen()
    monkeypatch.setattr(app_module, "provider_generate", fake_streamer)

    r = await client.post("/chat", json={"message": "stream please", "agent": "general", "stream": True})
    # We expect 200 because app swallows mid-stream exceptions (fix A)
    assert r.status_code == 200
    assert "partial " in r.text

    # We also expect an error to be logged by logger.exception()
    # The exact message depends on your code; check a substring:
    log_text = "\n".join(rec.getMessage() for rec in caplog_info.records)
    assert "Streaming error occurred" in log_text or "Client disconnected" in log_text or "network dropped" in log_text
