from fastapi import Request
from app.services.memory import MemoryStore

def get_memory_store(request: Request) -> MemoryStore:
    return request.app.state.memory_store
