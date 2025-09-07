# Pi FastAPI Agent Server

Lightweight multi-agent server built on **FastAPI**, designed to run on Raspberry Pi.  
Current version: 0.4.0 (**Phase 2**) — single agent, Ollama provider, stream and non-stream `/chat`, short conversation memory.

---

## Docs Contents

  ## Contents
  - [01. app.py](/docs/app_py.md)
  - [02. agents/*](/docs/agents.md)
  - [03. providers/*](/docs/providers.md)
  - [04. config](/docs/config.md)
  - [05. memory](/docs/memory.md)
  - [06. Streaming](/docs/streaming.md)


---

## Project Structure

```
agents/
  app/
    __init__.py
    main.py                    # FastAPI factory, CORS, router include, app.state wiring

    core/
      __init__.py
      config.py                # .env-backed settings (provider, model, limits, memory toggles)
      logging.py               # basic logging config (optional but useful)

    api/
      __init__.py
      deps.py                  # lightweight dependency providers (e.g., MemoryStore)
      routers/
        __init__.py
        health.py              # GET /health
        agents.py              # GET /agents
        chat.py                # POST /chat (stream + non-stream)

    schemas/
      __init__.py
      chat.py                  # ChatRequest / ChatResponse

    services/
      __init__.py
      memory.py                # TTL + LRU memory store (async + locks)
      prompt.py                # build_prompt() and history rendering
      chat_service.py          # glue: loads system prompt, builds prompt, calls provider

    providers/
      __init__.py
      base.py                  # ProviderError + interface type
      factory.py               # selects provider by config
      ollama.py                # Ollama implementation (stream + non-stream)

    agents/
      __init__.py
      general.py               # loads prompts/general_system.txt

    prompts/
      general_system.txt       # your system prompt

  tests/                       # (unchanged for now; update imports if you rename top package)

  .env
  requirements.txt
  requirements-dev.txt
  README.md
  pyproject.toml               # (optional) if you want modern tooling

```


## Packages

### app/main.py
- creates the fastapi app, adds CORS, wires the in-memory store, and includes all routers.
---

### app/core/
- *config.py*
  loads *.env* values. Routers, services, and providers import constants from core.config instead of hardcoding values.
- *logging.py*
a place for global logging setup (TODO)
---

### app/api/
- *deps.py* exposes the MemoryStore from app.state so routers can use it via Depends(...)
- *routers/* entry points
How it connects:
routers call directly into the services layer (never directly into providers), and use schemas for request/response contracts.Dependencies from deps.py inject shared objects (like memory).
---

### app/schemas/
- *chat.py* pydantic models that define the API contracts (ChatRequest and ChatResponse)
- Routers validate input/output via these models.
---

### app/services/
Domain logic independent from HTTP details.
- memory.py A TTL + max-turns, async-safe conversation store using a dict of deques.
- prompt.py Renders prior chat with the agent and system prompt into a single model-friendly prompt string for chat history context
- *chat_service.py*
  The glue:
  - pulls history (if memory enabled)
  - loads the agent's system prompt
  - builds the final prompt
  - calls the selected provider (via *factory*) with options
How it all connects:
- Routers call chat_service.prepare_and_generate(...), which returns (conversation_id, prompt, result) where result is either a string (non-stream) or an async iterator (stream). Routers then write to memory and serialize responses.
---

### app/providers/
Abstractions for LLMs, clean seam to swap/expand providers
- *base.py* Defines ProviderError and the generate(...) interface (returning either a string or async iterator of strings).
- *factory.py* Chooses the active provider based on core.config.PROVIDER (e.g., “ollama”). This keeps routers/services ignorant of provider details.
- *ollama.py* 
  Concrete implementation:
  - Non-stream: POST to */api/generate*, return response field.
  - Stream: *client.stream()* lines, parse JSON per line, yield token chunks.
  - Uniform error handling (raise_for_status, provider-level error strings).
How it connects:
- services/chat_service.py asks factory.get_generate() for the right function; no other layer needs to know which backend is in use.
---

### Request flow (nonstream)
- 1) Client -> /chat with {message, agent, stream:false}
- 2) Router (*api/routers/chat.py*)
    - validates *ChatRequest*
    - Grabs *MemoryStore* via *Depends(get_memory_store)*
    - Calls *services.chat_service.prepare_and_generate(...)*
- 3) Service (*chat_service.py*)
    - Reads config toggles from *core.config*
    - Fetches past turns from *services.memory* (if enabled)
    - Loads system prompt from *agents.general*
    - Builds final prompt via *services.prompt*
    - Gets provider *generate* from *providers.factory → providers.ollama*
    - Awaits a string reply
- 4. Router
    - Appends user turn + assistant reply to memory
    - Returns a *ChatResponse* JSON
---

### Request flow (stream)
Same steps 1–3, except the provider returns an async iterator.
The router wraps it in StreamingResponse, yielding chunks; on completion (or disconnect) it appends the concatenated assistant reply to memory.
---

## Requirements

Current `requirements.txt`:

```
fastapi==0.112.2
uvicorn[standard]==0.30.6
httpx==0.27.2
python-dotenv==1.0.1
pydantic==2.8.2
```
---

# Code

agents/general.py
```python
from pathlib import Path

def load_system_prompt() -> str:
    p = Path(__file__).resolve().parents[1] / "prompts" / "general_system.txt"
    return p.read_text(encoding="utf-8").strip()

```
```python
# api/deps.py
from fastapi import Request
from app.services.memory import MemoryStore

def get_memory_store(request: Request) -> MemoryStore:
    return request.app.state.memory_store
```

```python
# api/routers/agents.py
from fastapi import APIRouter

router = APIRouter(tags=["agents"])

@router.get("/agents")
def list_agents() -> dict:
    # Single built-in agent for now; easy to extend later
    return {"agents": ["general"]}
```
```python
# api/routers/chat.py
import logging
from typing import AsyncIterator, cast
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.api.deps import get_memory_store
from app.services.memory import MemoryStore
from app.core import config
from app.providers.base import ProviderError
from app.services.chat_service import prepare_and_generate

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)
ALLOWED_AGENTS = {"general"}

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request, memory: MemoryStore = Depends(get_memory_store)):
    if req.agent not in ALLOWED_AGENTS:
        raise HTTPException(status_code=400, detail="unknown agent")

    try:
        convo_id, _prompt, result = await prepare_and_generate(
            message=req.message,
            agent=req.agent,
            conversation_id=req.conversation_id,
            memory=memory if config.ENABLE_MEMORY else None,
            stream=req.stream,
        )
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Non-stream path
    if not req.stream:
        reply = cast(str, result)
        if config.ENABLE_MEMORY:
            await memory.append(convo_id, "user", req.message)
            await memory.append(convo_id, "assistant", reply)
        return ChatResponse(
            reply=reply,
            conversation_id=convo_id,
            model=config.OLLAMA_MODEL_GENERAL,
            provider=config.PROVIDER,
        )

    # Stream path
    gen = cast(AsyncIterator[str], result)

    async def streamer():
        acc: list[str] = []
        try:
            async for chunk in gen:
                acc.append(chunk)
                if await request.is_disconnected():
                    logger.info("client disconnected, stopping stream")
                    break
                yield chunk.encode("utf-8")
        except Exception as e:
            logger.exception("streaming error occurred: %s", e)
        finally:
            if config.ENABLE_MEMORY:
                await memory.append(convo_id, "user", req.message)
                if acc:
                    await memory.append(convo_id, "assistant", "".join(acc))

    headers = {"X-Conversation-Id": convo_id}
    return StreamingResponse(streamer(), media_type="text/plain; charset=utf-8", headers=headers)
```
```python
# api/routers/health.py
from fastapi import APIRouter

router = APIRouter(tags=["meta"])

@router.get("/health")
def health():
    return {"status": "ok"}
```
```python
#core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

#Provider
PROVIDER = os.getenv("PROVIDER", "ollama")
OLLAMA_MODEL_GENERAL = os.getenv("OLLAMA_MODEL_GENERAL", "qwen2.5:3b-instruct")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

#Generation caps
CTX_TOKENS = int(os.getenv("CTX_TOKENS", "2048"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "200"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

#Memory
ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() in {"1", "true", "yes", "y"}
MEMORY_MAX_TURNS = int(os.getenv("MEMORY_MAX_TURNS", "8"))
MEMORY_TTL_MIN = int(os.getenv("MEMORY_TTL_MIN", "60"))
MEMORY_MAX_CONVERSATIONS = int(os.getenv("MEMORY_MAX_CONVERSATIONS", "500"))
```
```python
# providers/base.py
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
```
```python
# providers/factory.py
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
```
```python
# providers/ollama.py
import json
import httpx
from typing import Optional, Dict, Any, AsyncIterator
from app.providers.base import ProviderError, GenerateReturn
from app.core import config

def _apply_defaults(options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    opts: Dict[str, Any] = dict(options or {})
    opts.setdefault("num_ctx", config.CTX_TOKENS)
    opts.setdefault("num_predict", config.MAX_TOKENS)
    opts.setdefault("temperature", config.TEMPERATURE)
    return opts

async def _generate_streaming(payload: Dict[str, Any]) -> AsyncIterator[str]:
    timeout = httpx.Timeout(120.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", f"{config.OLLAMA_HOST}/api/generate", json=payload) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(data.get("response"), str) and data["response"]:
                    yield data["response"]
                if data.get("error"):
                    raise ProviderError(f"Ollama error: {data['error']}")

async def generate(
    prompt: str,
    *,
    model: str,
    stream: bool = False,
    options: Optional[Dict[str, Any]] = None,
) -> GenerateReturn:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": _apply_defaults(options),
    }
    try:
        if stream:
            return _generate_streaming(payload)
        timeout = httpx.Timeout(60.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{config.OLLAMA_HOST}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            err = data.get("error")
            if isinstance(err, str) and err:
                raise ProviderError(f"Ollama error: {err}")
            reply = data.get("response", "")
            if not isinstance(reply, str):
                raise ProviderError("Unexpected response type from Ollama.")
            return reply
    except httpx.HTTPError as e:
        raise ProviderError(f"Ollama HTTP error: {e}") from e
```
```python
# schemas/chat.py
from pydantic import BaseModel, Field
from typing import Optional

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
```
```python
# services/chat_service.py
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
```
```python
# services/memory.py
from __future__ import annotations
from collections import deque
from typing import Deque, Dict, List, TypedDict
import asyncio
import time

class Turn(TypedDict): # each turn is a dict
    role: str
    content: str
    ts: float

class MemoryStore:
    def __init__(self, *, max_turns: int = 8, ttl_seconds: int = 3600, max_conversations: int = 500) -> None:
        """
        self._store: Holds the actual conversation history for each active conversation.
        Maps conversation_id (str) → deque of turns Deque[Turn]
        self._last: Tracks the last activity timestamp for each conversation.
        Maps conversation_id (str) → last activity timestamp (float)
        """
        self._store: Dict[str, Deque[Turn]] = {}
        self._last: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._max_turns = max(1, max_turns) # at least 1 turn per conversation
        self._ttl = max(0, ttl_seconds) # 0 means no TTL
        self._max_convos = max(1, max_conversations)


    """
    When the service needs to build a prompt:
    1. It calls memory.get(convo_id) to retrieve the list of turns for that conversation.
    2. The get method first checks if the conversation has expired based on TTL and prunes it if necessary.
    3. It then returns the list of turns (role, content, timestamp) for that conversation.
    4. The service uses this list to construct the prompt.
    5. If the conversation does not exist or has expired, an empty list is returned.
    6. The service can then handle this case appropriately (e.g., start a new conversation).
    """
    async def get(self, convo_id: str) -> List[Turn]:
        await self._maybe_prune(convo_id)
        async with self._lock:
            dq = self._store.get(convo_id)
            if not dq:
                return []
            self._last[convo_id] = time.time()
            return list(dq)

    # when a new message is added to a conversation, we append it to the deque inside self._store
    # we also update the last activity timestamp in self._last
    async def append(self, convo_id: str, role: str, content: str) -> None:
        now = time.time()
        async with self._lock:
            dq = self._store.get(convo_id)
            if dq is None:
                dq = deque(maxlen=self._max_turns)
                self._store[convo_id] = dq
            dq.append({"role": role, "content": content, "ts": now})
            self._last[convo_id] = now
            if len(self._store) > self._max_convos:
                oldest = min(self._last.items(), key=lambda kv: kv[1])[0]
                self._store.pop(oldest, None)
                self._last.pop(oldest, None)
    
    # check if a conversation has expired based on TTL and prune it if necessary
    # if ttl is 0 or negative, we skip pruning
    async def _maybe_prune(self, convo_id: str) -> None:
        if self._ttl <= 0:
            return
        now = time.time()
        ts = self._last.get(convo_id)
        if ts and (now - ts) > self._ttl:
            async with self._lock:
                self._store.pop(convo_id, None)
                self._last.pop(convo_id, None)
```
```python
# services/prompt.py
from typing import List, Dict, Iterable

def _render_history(history: Iterable[Dict[str, str]]) -> str:
    parts: List[str] = []
    for turn in history:
        role = (turn.get("role") or "").strip().lower()
        content = turn.get("content") or ""
        if not content:
            continue
        if role == "assistant":
            parts.append(f"<assistant>\n{content}\n</assistant>")
        else:
            parts.append(f"<user>\n{content}\n</user>")
    return "\n".join(parts)

def build_prompt(system: str, user: str, history: List[Dict[str, str]] | None = None) -> str:
    hist = _render_history(history or [])
    if hist:
        return (
            f"<system>\n{system}\n</system>\n\n"
            f"{hist}\n\n"
            f"<user>\n{user}\n</user>"
        )
    return (
        f"<system>\n{system}\n</system>\n\n"
        f"<user>\n{user}\n</user>"
    )
```
```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import config
from app.api.routers.health import router as health_router
from app.api.routers.agents import router as agents_router
from app.api.routers.chat import router as chat_router
from app.services.memory import MemoryStore


def create_app() -> FastAPI:
    app = FastAPI(title="Pi Agent Server", version="0.4.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    """
app.state is a built-in FastAPI mechanism to store shared objects.
We put MemoryStore there so it exists once and is accessible from any router or service.
Access it safely using a Depends() injection pattern, not as a bare global.
read Q&A.
    """
    app.state.memory_store = MemoryStore(
        max_turns=config.MEMORY_MAX_TURNS,
        ttl_seconds=config.MEMORY_TTL_MIN * 60,
        max_conversations=config.MEMORY_MAX_CONVERSATIONS,
    )

    # Routers
    app.include_router(health_router)
    app.include_router(agents_router)
    app.include_router(chat_router)

    return app


app = create_app()
```






