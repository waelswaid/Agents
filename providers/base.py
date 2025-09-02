# let's us swap/add providers later without touching endpoint logic (local/openai/deepseek...)
from typing import Optional, Dict, Any

class ProviderError(Exception):
    pass

# abstract abstract function signature every provider must implement
async def generate(prompt: str, *, model: str, stream: bool = False,
                   options: Optional[Dict[str, Any]] = None) -> str:
    """
    Abstract provider interface. Implemented in providers/ollama.py later.
    Returns a single string when stream=False.
    """
    raise NotImplementedError