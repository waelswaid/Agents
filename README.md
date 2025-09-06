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

Current `requirements-dev.txt`:
```
pytest==8.3.2
pytest-asyncio==0.23.8
respx==0.21.1
anyio==4.4.0
```
---




