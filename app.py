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

# Provider switch
if config.PROVIDER == "ollama":
    from providers.ollama import generate as provider_generate

# TODO when I implement more providers a simple if else wouldn't be enough and should be changed.
else:
    from providers.base import generate as provider_generate  # placeholder; raises NotImplemented

# creates FastAPI instance
app = FastAPI(title="Pi Agent Server", version="0.2.0")

# simple liveness check
@app.get("/health")
def health() -> dict:
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
    message: str = Field(..., min_length=1, max_length=4000)
    agent: str = Field("general", description="Only 'general' in Phase 1")
    stream: bool = False

class ChatResponse(BaseModel):
    reply: str
    model: str
    provider: str




@app.post("/chat", response_model=ChatResponse) # this line does two things at once, (1) @app.post("\chat") -> tells fastapi when the client sends
#http POST request to /chat, run this function.
#(2) response_model=ChatResponse -> whatever this function returns must be validated and shaped like ChatResponse.


async def chat(req: ChatRequest) -> ChatResponse: # (3)async function, input is validated against ChatRequest model.
    #(3) allows the function to pause and wait (with await) for slow operations without blocking the entire server.
    # if 10 users hit /chat at once, this allows the server to juggle them concurrently, without async it would proccess them one by one
    if req.agent != "general":
        raise HTTPException(status_code=400, detail="Unknown agent (only 'general' supported in Phase 1)")

    system = load_system_prompt()
    prompt = build_prompt(system, req.message)

    # Map simple options to Ollama
    options: Dict[str, Any] = {
        "temperature": config.TEMPERATURE,
        "num_ctx": config.CTX_TOKENS,
        "num_predict": config.MAX_TOKENS,
    }

    try:
        reply = await provider_generate( # calls the provider with the prompt.
            prompt,
            model=config.OLLAMA_MODEL_GENERAL, # TODO ollama_model_general should be changed when more providers are added
            stream=False,  # Phase 1 = non-stream
            options=options,
        )
        return ChatResponse(# wrap provider output into ChatResponse schema
            reply=reply,
            model=config.OLLAMA_MODEL_GENERAL, # TODO this should also be changed.
            provider=config.PROVIDER,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Provider error: {e}")