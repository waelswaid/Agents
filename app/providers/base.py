# let's us swap/add providers later without touching endpoint logic (local/openai/deepseek...)
# declares the abstract provider contract (generate(...)) that all providers must implement

from typing import Optional, Dict, Any, AsyncIterator, Union

class ProviderError(Exception):
    pass

GenerateReturn = Union[str, AsyncIterator[str]]

async def generate(
    prompt: str,
    *,
    model: str,
    stream: bool = False,
    options: Optional[Dict[str, Any]] = None,
) -> GenerateReturn:
    raise NotImplementedError
