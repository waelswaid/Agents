# let's us swap/add providers later without touching endpoint logic (local/openai/deepseek...)
# declares the abstract provider contract (generate(...)) that all providers must implement

from typing import Optional, Dict, Any, AsyncIterator, Union


# defines a provideerror for consistent error handling at the app layer so the api can distinguish provider faults from user errors
class ProviderError(Exception):
    pass


# When stream=False -> returns a single string
# When stream=True  -> returns an async iterator of text chunks
GenerateReturn = Union[str, AsyncIterator[str]]

async def generate(
    prompt: str,
    *,
    model: str,
    stream: bool = False,
    options: Optional[Dict[str, Any]] = None,
) -> GenerateReturn:
    """Abstract provider interface."""
    raise NotImplementedError  # implemented by providers/<name>.py