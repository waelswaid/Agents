# tests/conftest.py
import os
import asyncio
import logging
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Ensure test-friendly env (small TTL & windows)
os.environ.setdefault("ENABLE_MEMORY", "true")
os.environ.setdefault("MEMORY_TTL_MIN", "1")           # fast expiry window
os.environ.setdefault("MEMORY_MAX_TURNS", "3")         # small window
os.environ.setdefault("MEMORY_MAX_CONVERSATIONS", "3") # small LRU

# IMPORTANT: import the app after envs are set
import app as app_module  # your FastAPI app module


@pytest_asyncio.fixture
async def app():
    # Expose the FastAPI app object
    return app_module.app

@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def caplog_info(caplog):
    caplog.set_level(logging.INFO)
    return caplog

@pytest.fixture
def caplog_debug(caplog):
    caplog.set_level(logging.DEBUG)
    return caplog
