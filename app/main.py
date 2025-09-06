# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import config
from app.api.routers.health import router as health_router
from app.api.routers.agents import router as agents_router
from app.api.routers.chat import router as chat_router
from app.services.memory import MemoryStore


def create_app() -> FastAPI:
    app = FastAPI(title="Pi Agent Server", version="0.4.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    """
app.state is a built-in FastAPI mechanism to store shared objects.
We put MemoryStore there so it exists once and is accessible from any router or service.
Access it safely using a Depends() injection pattern, not as a bare global.
read Q&A.
    """
    app.state.memory_store = MemoryStore(
        max_turns=config.MEMORY_MAX_TURNS,
        ttl_seconds=config.MEMORY_TTL_MIN * 60,
        max_conversations=config.MEMORY_MAX_CONVERSATIONS,
    )

    # Routers
    app.include_router(health_router)
    app.include_router(agents_router)
    app.include_router(chat_router)

    return app


app = create_app()



