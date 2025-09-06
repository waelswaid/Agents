from typing import Callable, Awaitable, Optional, Dict, Any, AsyncIterator, Union
from app.core import config
from app.providers.base import ProviderError, GenerateReturn

GenerateFn = Callable[[str], Awaitable[GenerateReturn]]

async def _not_implemented(*args, **kwargs) -> GenerateReturn:
    raise ProviderError(f"Unknown provider: {config.PROVIDER}")

def get_generate():
    if config.PROVIDER == "ollama":
        from app.providers.ollama import generate
        return generate
    return _not_implemented
