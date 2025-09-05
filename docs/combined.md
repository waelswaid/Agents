# This file contains all the documentation and code of the project combined

---

## Project Structure

```
agents/
  base.py            # prompt builder
  general.py         # general agent system prompt loader
providers/
  base.py            # provider contract + ProviderError
  ollama.py          # Ollama provider implementation (non-stream)
prompts/
  general_system.txt # system prompt for the general agent
utils/
  config.py          # centralized configuration loader
  memory.py
app.py               # FastAPI entry point (endpoints & routing)
.env                 # environment variables (not committed)
.gitignore
requirements.txt
README.md
```

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

## .env

Current `.env`:

```
# Provider
PROVIDER=ollama
OLLAMA_MODEL_GENERAL=qwen2.5:3b-instruct
OLLAMA_HOST=http://127.0.0.1:11434

# Limits
CTX_TOKENS=2048
MAX_TOKENS=200
TEMPERATURE=0.7

# Phase 2 memory
ENABLE_MEMORY=true
MEMORY_MAX_TURNS=8
MEMORY_TTL_MIN=60
MEMORY_MAX_CONVERSATIONS=500
```
---

# `app.py` — Documentation



## 1) High‑Level Overview


At a glance, the `app.py` file does three big things:

1. **Sets up the web server** using FastAPI: defines endpoints like `/health`, `/agents`, and `/chat`.
2. **Loads configuration and helpers**: provider selection, prompt building, and the in‑memory memory store.
3. **Implements the `/chat` endpoint** that:
   - Builds the model prompt (system + short memory + current user message)
   - Calls the model provider (Ollama) in **non‑stream** or **stream** mode
   - Updates short memory when the model responds
   - Returns JSON (non‑stream) or a live **token stream** (streaming)


## 2) Creating the FastAPI App & Memory Store


You initialize the FastAPI app with a title and version, then create a **MemoryStore** for short‑term memory.

```python
app = FastAPI(title="Pi Agent Server", version="0.3.0")

_memory = MemoryStore(
    max_turns=config.MEMORY_MAX_TURNS,
    ttl_seconds=config.MEMORY_TTL_MIN * 60,
    max_conversations=config.MEMORY_MAX_CONVERSATIONS,
)
```
- **`FastAPI(...)`**: configures the app metadata (helpful for docs, logs).
- **`MemoryStore(...)`**: keeps a deque (fixed‑length list) of recent turns per `conversation_id`:
  - `max_turns` → how many turns to keep
  - `ttl_seconds` → prune idle conversations
  - `max_conversations` → global cap (evict oldest if exceeded)

> If `ENABLE_MEMORY=false` in `.env`, the app simply **skips reading/writing** to this store.


## 2.1) Configuration Dependencies
```python
from utils.config import (
    OLLAMA_MODEL_GENERAL,
    TEMPERATURE,
    CTX_TOKENS,
    MAX_TOKENS,
    ENABLE_MEMORY
)
```

## 3) Request/Response Models (Pydantic)


```python
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
- **`ChatRequest`**: clients send a `message`, optional `agent`, a `stream` flag, and optionally an existing `conversation_id`.
- **`ChatResponse`**: server returns a `reply` and the `conversation_id`. We kept `model`/`provider` **optional** so you can omit them without errors.

## 4) Small Endpoints: `/health` and `/agents`


**`GET /health`** — Lightweight liveness check:

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

**`GET /agents`** — A simple list of available agents (for now, just `general`). You may return either a list or an object; here’s an object form:

```python
@app.get("/agents")
def agents():
    return {"agents": ["general"]}
```

## 5) `/chat` Endpoint


The heart of the server: receives a message, builds a prompt, calls the provider, and returns a response.
It supports both **non‑stream** and **stream** modes.

### 5.1 Handler signature and conversation ID


```python
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    convo_id = req.conversation_id or str(uuid4())
```
- The **function is async** so we can await I/O (HTTP calls to the provider).
- If the client didn’t send a `conversation_id`, we create a new one (`uuid4`).

### 5.2 Load short memory

```python
history = []
if config.ENABLE_MEMORY:
    history = await _memory.get(convo_id)
```
- Reads recent turns (a few user/assistant messages) for this conversation.
- This *history* will be placed **before** the new message so the model remembers context.

### 5.3 Build the final prompt (system + history + user)


```python
system = load_system_prompt()
prompt = build_prompt(system, req.message, history)
```
- **`load_system_prompt()`** loads your agent’s top‑level instructions (style, safety, tone).
- **`build_prompt(...)`** combines everything:
  1. `<system>…</system>`
  2. `<user>…</user>` / `<assistant>…</assistant>` blocks from recent history
  3. `<user>NEW_MESSAGE</user>`

### 5.4 Options sent to the provider


```python
options = {
    "temperature": config.TEMPERATURE,
    "num_ctx": config.CTX_TOKENS,
    "num_predict": config.MAX_TOKENS,
}
```
These are mapped to the provider (Ollama) under `options` in the JSON payload.
They control generation style and **hard caps** to preserve performance on a Pi.

### 5.5 Non‑stream path 


```python
if not req.stream:
    try:
        reply = await provider_generate(
            prompt, model=config.OLLAMA_MODEL_GENERAL, stream=False, options=options
        )
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Update memory with the user question and assistant reply
    if config.ENABLE_MEMORY:
        await _memory.append(convo_id, "user", req.message)
        await _memory.append(convo_id, "assistant", reply)

    return ChatResponse(
        reply=reply,
        conversation_id=convo_id,
        # model=config.OLLAMA_MODEL_GENERAL,
        # provider=config.PROVIDER,
    )
```
- Calls the provider and waits for a **single** final string (`stream=False`).
- On success, it **appends** both the user and assistant turns to conversation memory.
- It returns a JSON body including the `conversation_id` (so the client can reuse it).

### 5.6 Streaming path (live tokens)


```python
try:
    gen = await provider_generate(
        prompt, model=config.OLLAMA_MODEL_GENERAL, stream=True, options=options
    )
except ProviderError as e:
    raise HTTPException(status_code=502, detail=str(e))

async def streamer():
    acc = []
    try:
        async for chunk in gen:
            acc.append(chunk)
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
```
- We get an **async iterator** from the provider and wrap it in a **StreamingResponse**.
- Each time we receive a chunk, we `yield` it to the client immediately.
- If the client disconnects, we stop (saves CPU) and still save any **partial** answer.
- We return the `conversation_id` in a **response header** (`X‑Conversation‑Id`) so the client can continue the thread even during streams.


## 5.7) Response Headers
| Header | Description |
|--------|-------------|
| X-Conversation-Id | Unique conversation identifier |
| Content-Type | `application/json` or `text/plain; charset=utf-8` |


## 6) Provider Design


providers share a **common interface**:

```python
# providers/base.py
class ProviderError(Exception):
    pass

GenerateReturn = Union[str, AsyncIterator[str]]

async def generate(prompt: str, *, model: str, stream: bool = False, options: Optional[Dict[str, Any]] = None) -> GenerateReturn:
    raise NotImplementedError
```
- **Non‑stream** → returns a **string** with the full reply.
- **Stream** → returns an **async iterator of strings** (chunks).
- The app uses this uniformly and focuses on HTTP and memory, not on backend details.

## 7) Error Handling & HTTP Status Codes


- **`ProviderError` → `HTTPException(502)`**: clear separation between server and the provider (model backend). A 502 means the downstream model failed or was unreachable.
- **Validation errors (Pydantic)** → FastAPI returns **422** with details.
- **Unhandled exceptions** → FastAPI returns **500**; keep logs enabled for debugging.

## 8) Request Lifecycle


## Full Code

- app.py
```python
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

else:
    from providers.base import generate as provider_generate  # placeholder; raises NotImplemented



# creates FastAPI instance
app = FastAPI(title="Pi Agent Server", version="0.3.0")


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




@app.post("/chat", response_model=ChatResponse) 
async def chat(req: ChatRequest, request: Request): 
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
                    break
                yield chunk.encode("utf-8")
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
```
---

# Agents Module Documentation

## agents/agents_base.py

### Overview
The `base.py` module provides functionality for assembling chat prompts by combining system instructions, conversation history, and user messages using XML-style formatting.

### Functions

#### `_render_history(history: Iterable[Dict[str, str]]) -> str`
**Purpose:** Formats conversation history into XML-style blocks.

**Parameters:**
- `history` (Iterable[Dict[str, str]]): Collection of conversation turns, each containing:
  - `role`: Either "user" or "assistant"
  - `content`: The message content

**Returns:**
- `str`: Formatted history as string with XML-style tags



#### `build_prompt(system: str, user: str, history: List[Dict[str, str]] | None = None) -> str`
**Purpose:** Assembles a complete prompt combining system instructions, chat history, and current user message.

**Parameters:**
- `system` (str): System instructions/rules for the model (generated in agents/general.py)
- `user` (str): Current user message
- `history` (List[Dict[str, str]] | None): Optional conversation history

**Returns:**
- `str`: Complete formatted prompt with XML-style tags

## Full Code

- agents/agents_base.py

```python
"""
provides the generic function that assembles a chat prompt from:

* a system block (behaviour/rules)
* a user block (the user's message)
* a placeholder for future chat history

"""

from typing import List, Dict, Iterable

def _render_history(history: Iterable[Dict[str, str]]) -> str:
    parts: List[str] = []
    for turn in history:
        role = turn.get("role", "").strip().lower()
        content = turn.get("content", "")
        if not content:
            continue
        if role == "assistant": # response from the model
            parts.append(f"<assistant>\n{content}\n</assistant>")
        else:
            parts.append(f"<user>\n{content}\n</user>")
    return "\n".join(parts)

def build_prompt(system: str, user: str, history: List[Dict[str, str]] | None = None) -> str:
    """
    Prompt composer with optional short history:
    <system>...</system>
    <user/assistant history...>
    <user>...</user>
    """
    hist = _render_history(history or [])
    # contains the formatted conversation history that provides context for the model's next response
    if hist:
        return (
            f"<system>\n{system}\n</system>\n\n"
            f"{hist}\n\n"
            f"<user>\n{user}\n</user>"
        )
    else:
        return (
            f"<system>\n{system}\n</system>\n\n"
            f"<user>\n{user}\n</user>"
        )
```


## agents/agents_general.py

### Overview
- loads prompts/general_system.txt for the general agent from the prompts/ folder

## Full Code

- agents/agents_general.py

```python
# load the system prompt text for the general agent from the prompts/ folder
from pathlib import Path

def load_system_prompt() -> str:
    p = Path(__file__).resolve().parents[1] / "prompts" / "general_system.txt"
    return p.read_text(encoding="utf-8").strip()

```
---

# config.py Documentation

## Overview
The `utils/config.py` module manages environment-based configuration for the agent server, providing defaults and type-safe configuration values.

## Environment Variables

### Provider Settings
- `PROVIDER` (str): LLM provider selection (default: "ollama")
- `OLLAMA_MODEL_GENERAL` (str): Default Ollama model (default: "qwen2.5:3b-instruct")
- `OLLAMA_HOST` (str): Ollama API endpoint (default: "http://127.0.0.1:11434")

### Memory Configuration
- `ENABLE_MEMORY` (bool): Toggle conversation memory (default: true)
- `MEMORY_MAX_TURNS` (int): Messages kept per conversation (default: 8)
- `MEMORY_TTL_MIN` (int): Conversation timeout in minutes (default: 60)
- `MEMORY_MAX_CONVERSATIONS` (int): Maximum concurrent conversations (default: 500)

### Model Parameters
- `CTX_TOKENS` (int): Context window size (default: 4096)
- `MAX_TOKENS` (int): Maximum tokens to generate (default: 1024)
- `TEMPERATURE` (float): Response randomness (default: 0.7)

## Functions

### `load_dotenv()`
**Purpose:** Loads environment variables from `.env` file if present

**Example:**
```python
# .env file
OLLAMA_MODEL_GENERAL=llama2:13b
TEMPERATURE=0.5
```

## Implementation Notes
- Uses `python-dotenv` for .env file support
- Provides sensible defaults for all values
- Type conversion for numeric values
- Boolean parsing supports various formats ("true", "1", "yes", "y")
- Environment variables take precedence over defaults

## Usage Example
```python
from utils.config import OLLAMA_HOST, TEMPERATURE

client = OllamaClient(host=OLLAMA_HOST)
response = await client.generate(
    prompt="Hello",
    temperature=TEMPERATURE
```

## Full Code
- utils/config.py
```python
# centralized configuration loader
# runs load_dotenv() to read .env
# decouples code from environment we can swap models/hosts/limits without code change

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env if present

PROVIDER = os.getenv("PROVIDER", "ollama") # TODO when more providers are added this should be changed to a list
OLLAMA_MODEL_GENERAL = os.getenv("OLLAMA_MODEL_GENERAL", "qwen2.5:3b-instruct")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")


                                    # ---- Phase 2 additions -----

# toggle short term memory (in-memory only)
ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() in {"1", "true", "yes", "y"}

#how many recent turns to keep per conversation (user/assistant pairs)
MEMORY_MAX_TURNS = int(os.getenv("MEMORY_MAX_TURNS", "8"))

#prune if idle for N minutes (O=no TTL)
MEMORY_TTL_MIN = int(os.getenv("MEMORY_TTL_MIN", "60"))

# bound total conversations to avoid pi RAM creep (LRU eviction)
MEMORY_MAX_CONVERSATIONS = int(os.getenv("MEMORY_MAX_CONVERSATIONS", "500"))




# simple caps; we'll enforce these later
CTX_TOKENS = int(os.getenv("CTX_TOKENS", "2048"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "200"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
```
---

# Memory Module Documentation

## Overview
The `utils/memory.py` module implements a lightweight, thread-safe, in-memory conversation store designed for Raspberry Pi constraints. It provides TTL-based expiration and LRU eviction.

## Classes

### `Turn`
**Purpose:** TypedDict for conversation turn structure

**Fields:**
- `role` (str): Message source ("user" or "assistant")
- `content` (str): Message text
- `ts` (float): Unix timestamp of message

**Example:**
```python
turn: Turn = {
    "role": "user",
    "content": "Hello!",
    "ts": 1693743200.0
}
```

### `MemoryStore`
**Purpose:** Thread-safe conversation manager with size and time limits

**Constructor Parameters:**
- `max_turns` (int): Messages per conversation (default: 8)
- `ttl_seconds` (int): Conversation timeout (default: 3600)
- `max_conversations` (int): Total conversations (default: 500)

#### Methods

##### `async def get(convo_id: str) -> List[Turn]`
**Purpose:** Retrieve conversation history

**Parameters:**
- `convo_id` (str): Unique conversation identifier

**Returns:**
- List of Turn objects or empty list if not found

**Example:**
```python
turns = await memory.get("abc-123")
```

##### `async def append(convo_id: str, role: str, content: str) -> None`
**Purpose:** Add message to conversation

**Parameters:**
- `convo_id` (str): Conversation identifier
- `role` (str): Message source
- `content` (str): Message text

**Example:**
```python
await memory.append("abc-123", "user", "Hello!")
```

##### `async def _maybe_prune(convo_id: str) -> None`
**Purpose:** Internal method to handle TTL expiration

**Parameters:**
- `convo_id` (str): Conversation to check

## Implementation Notes

### Memory Management
- Uses `collections.deque` with maxlen for automatic turn pruning
- Thread-safe operations via `asyncio.Lock()`
- TTL expiration checked on access
- LRU eviction when max conversations reached

### Storage Structure
```python
self._store: Dict[str, Deque[Turn]]  # Conversations
self._last: Dict[str, float]         # Access timestamps
```

### Example Usage
```python
memory = MemoryStore(
    max_turns=8,
    ttl_seconds=3600,
    max_conversations=500
)

# Add messages
await memory.append("conv1", "user", "Hello")
await memory.append("conv1", "assistant", "Hi!")

# Get history
turns = await memory.get("conv1")
```

## Full Code

- utils/memory.py
```python
from __future__ import annotations
from collections import deque
from typing import Deque, Dict, List, TypedDict
import asyncio # uses async/wait to handle concurrent requests
import time

class Turn(TypedDict): # class for creating fixed structure dicts
    role: str         # "user" | "assistant"
    content: str       # the message
    ts: float         # timestamp

class MemoryStore:
    """
    Very small, Pi-friendly in-memory conversation store.
    - Per-conversation deque capped by max_turns
    - Optional TTL eviction
    - LRU cap on total conversations
    """
    def __init__(
        self,
        *,
        max_turns: int = 8, # Maximum number of messages kept per conversation
        ttl_seconds: int = 60 * 60, # Time-to-live for conversations in seconds
        max_conversations: int = 500, # Maximum number of concurrent conversations, When limit is reached, oldest conversation is removed

    ) -> None:
        self._store: Dict[str, Deque[Turn]] = {} # Stores all conversations
        self._last: Dict[str, float] = {} # Last access time for each conversation (used for TTL and LRU eviction)
        self._lock = asyncio.Lock() # Prevents race conditions during concurrent access
        self._max_turns = max(1, max_turns)
        self._ttl = max(0, ttl_seconds)
        self._max_convos = max(1, max_conversations)

    # this method is used to retrieve conversation history
    async def get(self, convo_id: str) -> List[Turn]:
        await self._maybe_prune(convo_id) # Check and remove if expired
        dq = self._store.get(convo_id) # Get conversation queue
        return list(dq) if dq else [] # return active conversations

    # this method is used to append a new message to the conversation
    async def append(self, convo_id: str, role: str, content: str) -> None:
        now = time.time()
        async with self._lock:
            dq = self._store.get(convo_id)#gets existing convos
            if dq is None:#if there are none
                dq = deque(maxlen=self._max_turns) #creates new one with max turns
                self._store[convo_id] = dq 
            dq.append({"role": role, "content": content, "ts": now})
            self._last[convo_id] = now # update last access time
            # LRU eviction if we exceed the global limit
            if len(self._store) > self._max_convos:
                oldest = min(self._last.items(), key=lambda kv: kv[1])[0]
                self._store.pop(oldest, None)
                self._last.pop(oldest, None)

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
---

# prompts module documentation

## overview
contains a single prompt inside general_system.txt

### contents

- prompts/general_text.txt
```text
you are a helpful and efficient assistant. keep answers concise unless asked for depth.
```
---

# Providers Module Documentation
---
## providers/providers_base.py

### Overview
Defines the base provider contract and error handling for LLM interactions.

### Classes

#### `ProviderError`
**Purpose:** Custom exception for provider-specific errors.

**Attributes:**
- `message` (str): Error description
- `status_code` (int): HTTP status code (defaults to 502)

**Example:**
```python
raise ProviderError("Failed to connect to LLM", status_code=503)
```

### Types

#### `GenerateReturn`
**Purpose:** Type alias for provider response formats.
```python
GenerateReturn = Union[str, AsyncIterator[str]]
```
- `str`: Complete response for non-streaming
- `AsyncIterator[str]`: Token stream for streaming

## Full Code

- providers/providers_base.py
```python
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
```

---

## providers/providers_ollama.py

### Overview
Implements the Ollama API provider with streaming and non-streaming support.

### Functions

#### `_apply_defaults(options: Optional[Dict[str, Any]]) -> Dict[str, Any]`
**Purpose:** Applies default configuration values to Ollama request options.

**Parameters:**
- `options` (Optional[Dict[str, Any]]): Custom options

**Returns:**
- Dictionary with complete Ollama configuration

**Example:**
```python
opts = _apply_defaults({"temperature": 0.7})
# Returns: {"temperature": 0.7, "num_ctx": 4096, "num_predict": 1024}
```

#### `_generate_streaming(payload: Dict[str, Any]) -> AsyncIterator[str]`
**Purpose:** Handles streaming responses from Ollama API.

**Parameters:**
- `payload` (Dict[str, Any]): Request body for Ollama

**Returns:**
- `AsyncIterator[str]`: Stream of text chunks

**Example:**
```python
async for chunk in _generate_streaming({"prompt": "Hello", "model": "qwen:3b"}):
    print(chunk)
```

#### `generate(prompt: str, *, model: str, stream: bool = False, options: Optional[Dict[str, Any]] = None) -> GenerateReturn`
**Purpose:** Main generation function, wraps Ollama's /api/generate endpoint.

**Parameters:**
- `prompt` (str): Input text
- `model` (str): Model identifier
- `stream` (bool): Enable streaming mode
- `options` (Optional[Dict[str, Any]]): Custom configuration

**Returns:**
- `str` or `AsyncIterator[str]` depending on stream mode

**Example:**
```python
# Non-streaming
response = await generate("Hello!", model="qwen:3b")

# Streaming
async for chunk in await generate("Hello!", model="qwen:3b", stream=True):
    print(chunk)
```

## Full Code

- providers/providers_ollama.py
```python
import json
import httpx
from typing import Optional, Dict, Any, AsyncIterator, Union
from providers.base import ProviderError, GenerateReturn
from utils.config import (
    OLLAMA_HOST,
    CTX_TOKENS,
    MAX_TOKENS,
    TEMPERATURE,
)

def _apply_defaults(options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    opts: Dict[str, Any] = dict(options or {})
    # map server caps to Ollama options if caller didn’t set them
    opts.setdefault("num_ctx", CTX_TOKENS)
    opts.setdefault("num_predict", MAX_TOKENS)
    opts.setdefault("temperature", TEMPERATURE)
    return opts

async def _generate_streaming(payload: Dict[str, Any]) -> AsyncIterator[str]:
    timeout = httpx.Timeout(120.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", f"{OLLAMA_HOST}/api/generate", json=payload) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    # ignore malformed lines
                    continue
                # normal chunks carry 'response'; a final line has 'done': true
                chunk = data.get("response")
                if isinstance(chunk, str) and chunk:
                    yield chunk
                # if the server reports an error mid-stream, stop early
                if data.get("error"):
                    raise ProviderError(f"Ollama error: {data['error']}")

async def generate(
    prompt: str,
    *,
    model: str,
    stream: bool = False,
    options: Optional[Dict[str, Any]] = None,
) -> GenerateReturn:
    """
    Ollama /api/generate wrapper.
    - stream=False: returns full string
    - stream=True : returns async iterator of text chunks
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": _apply_defaults(options),
    }
    try:
        if stream:
            return _generate_streaming(payload)
        # non-stream path
        timeout = httpx.Timeout(60.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            reply = data.get("response", "")
            if not isinstance(reply, str):
                raise ProviderError("Unexpected response type from Ollama.")
            return reply
    except httpx.HTTPError as e:
        raise ProviderError(f"Ollama HTTP error: {e}") from e
```
---

