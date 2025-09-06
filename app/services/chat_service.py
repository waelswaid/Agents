from typing import Dict, Any, AsyncIterator, cast
from uuid import uuid4
from app.core import config
from app.services.prompt import build_prompt
from app.services.memory import MemoryStore
from app.providers.base import ProviderError
from app.providers.factory import get_generate
from app.agents.general import load_system_prompt

async def prepare_and_generate(
    *,
    message: str,
    agent: str,
    conversation_id: str | None,
    memory: MemoryStore | None,
    stream: bool,
) -> tuple[str, str, AsyncIterator[str] | str]:
    # ensure conversation id
    convo_id = conversation_id or str(uuid4())

    # history
    history = []
    if config.ENABLE_MEMORY and memory is not None:
        history = await memory.get(convo_id)

    system = load_system_prompt()
    prompt = build_prompt(system, message, history)

    options: Dict[str, Any] = {
        "temperature": config.TEMPERATURE,
        "num_ctx": config.CTX_TOKENS,
        "num_predict": config.MAX_TOKENS,
    }

    generate = get_generate()
    result = await generate(prompt, model=config.OLLAMA_MODEL_GENERAL, stream=stream, options=options)
    return convo_id, prompt, result  # result is str or AsyncIterator[str]
