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
else:
    from providers.base import generate as provider_generate  # placeholder; raises NotImplemented

app = FastAPI(title="Pi Agent Server", version="0.2.0")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.get("/agents")
def list_agents() -> dict:
    return {"agents": ["general"]}

# --------- Chat schema ---------
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    agent: str = Field("general", description="Only 'general' in Phase 1")
    stream: bool = False

class ChatResponse(BaseModel):
    reply: str
    model: str
    provider: str

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
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
        reply = await provider_generate(
            prompt,
            model=config.OLLAMA_MODEL_GENERAL,
            stream=False,  # Phase 1 = non-stream
            options=options,
        )
        return ChatResponse(
            reply=reply,
            model=config.OLLAMA_MODEL_GENERAL,
            provider=config.PROVIDER,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Provider error: {e}")