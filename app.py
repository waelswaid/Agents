"""
# imports config from utils/config.py
# loads the system prompt via agents/general.py
# composes a final prompt using agents/general.py
# calls the active provider's generate(...)
# maps environment caps (temp, num_ctx...) to provider options
# returns a typed response model or raises HTTPException on provider errors


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from utils import config
from agents.general import load_system_prompt
from agents.base import build_prompt
"""


from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, cast, AsyncIterator
from uuid import uuid4

from utils import config
from agents.general import load_system_prompt
from agents.base import build_prompt
from utils.memory import MemoryStore
from providers.base import ProviderError, GenerateReturn


# Provider switch
if config.PROVIDER == "ollama":
    from providers.ollama import generate as provider_generate

# TODO when I implement more providers a simple if else wouldn't be enough and should be changed.
else:
    from providers.base import generate as provider_generate  # placeholder; raises NotImplemented



# creates FastAPI instance
app = FastAPI(title="Pi Agent Server", version="0.3.0")


# --- Phase 2: tiny in-memory conversation store ---
_memory = MemoryStore(
    max_turns=config.MEMORY_MAX_TURNS,
    ttl_seconds=config.MEMORY_TTL_MIN * 60,
    max_conversations=config.MEMORY_MAX_CONVERSATIONS,
)


# simple liveness check
@app.get("/health")
def health():
    return {"status": "ok"}


# enumerate available agents
@app.get("/agents")
def list_agents() -> dict:
    return {"agents": ["general"]}


# --------- Chat schema ---------
"""
this is how FastAPI does validation (using these two classes). first class is what the client must send, second is what the api guarantees to return.
if the validation failsfastapi returns a '422 unprocessable entity' response with json body explaining the error.

BaseModel is the core pydantic package class that you inherit from when you want to define structured data models.
it provides data validation, type checking, and serialization automatically.
every model you create by subclassing BaseModel becomes a self-validating schema.
"""
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    agent: str = Field(default="general")
    stream: bool = Field(default=False)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: Optional[str] = None
    model: str
    provider: str




@app.post("/chat", response_model=ChatResponse) # this line does two things at once, (1) @app.post("\chat") -> tells fastapi when the client sends
#http POST request to /chat, run this function.
#(2) response_model=ChatResponse -> whatever this function returns must be validated and shaped like ChatResponse.


async def chat(req: ChatRequest, request: Request): # (3)async function, input is validated against ChatRequest model.
    #(3) allows the function to pause and wait (with await) for slow operations without blocking the entire server.
    # if 10 users hit /chat at once, this allows the server to juggle them concurrently, without async it would proccess them one by one
    # 
    # 
    # ensure conversation id
    convo_id = req.conversation_id or str(uuid4())

    # assemble history if enabled
    history = []
    if config.ENABLE_MEMORY:
        history = await _memory.get(convo_id)

    system = load_system_prompt()
    prompt = build_prompt(system, req.message, history)

    options: Dict[str, Any] = {
        "temperature": config.TEMPERATURE,
        "num_ctx": config.CTX_TOKENS,
        "num_predict": config.MAX_TOKENS,
    }

    # non-stream: keep old behavior
    if not req.stream:
        try:
            reply = cast(str, await provider_generate(
                prompt, model=config.OLLAMA_MODEL_GENERAL, stream=False, options=options
            ))
        except ProviderError as e:
            raise HTTPException(status_code=502, detail=str(e))
        # update memory
        if config.ENABLE_MEMORY:
            await _memory.append(convo_id, "user", req.message)
            await _memory.append(convo_id, "assistant", reply)
        return ChatResponse(reply=reply, conversation_id=convo_id)

    # stream path
    try:
        gen = cast(AsyncIterator[str], await provider_generate(
            prompt, model=config.OLLAMA_MODEL_GENERAL, stream=True, options=options
        ))
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))

    async def streamer() -> AsyncIterator[bytes]:
        # accumulate to store in memory after stream ends
        acc: list[str] = []
        try:
            async for chunk in gen:
                acc.append(chunk)
                # stop if client disconnected
                if await request.is_disconnected():
                    break
                yield chunk.encode("utf-8")
        finally:
            if config.ENABLE_MEMORY:
                await _memory.append(convo_id, "user", req.message)
                if acc:
                    await _memory.append(convo_id, "assistant", "".join(acc))

    headers = {"X-Conversation-Id": convo_id}
    return StreamingResponse(streamer(), media_type="text/plain; charset=utf-8", headers=headers)