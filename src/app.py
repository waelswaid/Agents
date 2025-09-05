from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, cast, AsyncIterator
from uuid import uuid4

from utils import config
from agents.agents_general import load_system_prompt
from agents.agents_base import build_prompt
from utils.memory import MemoryStore
from providers.providers_base import ProviderError, GenerateReturn
from fastapi.middleware.cors import CORSMiddleware
import logging


# Provider switch
if config.PROVIDER == "ollama":
    from providers.providers_ollama import generate as provider_generate

else:
    from providers.providers_base import generate as provider_generate  # placeholder; raises NotImplemented

logger = logging.getLogger(__name__)

# creates FastAPI instance
app = FastAPI(title="Pi Agent Server", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # List of origins that can access the API
    allow_methods=["*"],  # list of allowed HTTP methods
    allow_headers=["*"],  # list of allowed headers
)

ALLOWED_AGENTS = ["general"]

# in-memory conversation store
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
    model: Optional[str] = None
    provider: Optional[str] = None




@app.post("/chat", response_model=ChatResponse) # this line does two things at once, (1) @app.post("\chat") -> tells fastapi when the client sends
#http POST request to /chat, run this function.
#(2) response_model=ChatResponse -> whatever this function returns must be validated and shaped like ChatResponse.


async def chat(req: ChatRequest, request: Request): # (3)async function, input is validated against ChatRequest model.
    #(3) allows the function to pause and wait (with await) for slow operations without blocking the entire server.
    # if 10 users hit /chat at once, this allows the server to juggle them concurrently, without async it would proccess them one by one
    if req.agent not in ALLOWED_AGENTS:
        raise HTTPException(status_code=400, detail="unknown agent")
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
        return ChatResponse(reply=reply, conversation_id=convo_id, model=config.OLLAMA_MODEL_GENERAL, provider = config.PROVIDER,)

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
                    logger.info("client disconnected, stopping stream")
                    break
                yield chunk.encode("utf-8")
        except Exception as e:
            # log but ignore errors in streaming
            logger.exception("streaming error occured: %s", str(e))
        finally: # This block executes after streaming completes, whether it ends normally or due to an error
            if config.ENABLE_MEMORY:
                # Stores the user's original message
                await _memory.append(convo_id, "user", req.message)
                # If we accumulated any response chunks
                if acc:
                    # Join all chunks and store the complete assistant response
                    await _memory.append(convo_id, "assistant", "".join(acc))

    # set conversation ID header so client can track
    headers = {"X-Conversation-Id": convo_id}
    # text/event-stream is a standard for streaming text data over HTTP
    return StreamingResponse(streamer(), media_type="text/plain; charset=utf-8", headers=headers)