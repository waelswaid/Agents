# Phase 2 Short Memory


## 1) Concept: What “short memory” means


Short memory refers to the system remembering only the **recent tail** of a conversation instead of storing the entire dialogue forever.  
This is important for two reasons on a Raspberry Pi:

1. **Resource constraints** — Pi has limited RAM and CPU. Keeping unlimited chat history would quickly consume memory.
2. **Token constraints** — Language models have a fixed context window (`CTX_TOKENS`). If we pass too much history, we either overflow the context or waste tokens on very old turns.

So the server remembers only the **last N turns** (default 8) and optionally prunes old or idle conversations.  
This ensures:
- The model gets enough context for coherence (short-term memory).
- Resource usage is predictable and capped.

## 2) Configuration flags (.env → utils/config.py)

```python
ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() in {"1","true","yes","y"}
MEMORY_MAX_TURNS = int(os.getenv("MEMORY_MAX_TURNS", "8"))
MEMORY_TTL_MIN = int(os.getenv("MEMORY_TTL_MIN", "60"))
MEMORY_MAX_CONVERSATIONS = int(os.getenv("MEMORY_MAX_CONVERSATIONS", "500"))
```


**Explanation of each flag:**
- `ENABLE_MEMORY`: Turns the feature on or off. If `false`, every request is stateless, and only the current message is passed to the model.
- `MEMORY_MAX_TURNS`: How many turns (user+assistant exchanges) are kept in memory per conversation. If set to 8, the system keeps at most 8 most recent messages.
- `MEMORY_TTL_MIN`: Time-to-live for each conversation. If no new messages arrive for X minutes, the memory is cleared. This prevents idle sessions from lingering.
- `MEMORY_MAX_CONVERSATIONS`: Global cap. If too many distinct conversation_ids are active, the oldest one is evicted.

This combination guarantees we never blow up RAM usage and can precisely control how much history is retained.

## 3) Data structure: utils/memory.py

```python
class MemoryStore:
    def __init__(...):
        self._store: Dict[str, Deque[Turn]] = {}
        self._last: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._max_turns = max(1, max_turns)
        self._ttl = max(0, ttl_seconds)
        self._max_convos = max(1, max_conversations)
```


- `_store`: maps `conversation_id` → deque of turns (each turn is `{role, content, ts}`).
- `_last`: tracks the last activity timestamp for each conversation (used for TTL and LRU).
- `_lock`: ensures thread-safety for append and eviction.
- `_max_turns`: maximum turns per conversation (deque automatically drops oldest).
- `_ttl`: idle timeout in seconds (0 means disabled).
- `_max_convos`: global cap for number of conversations.

The **deque** data structure is important: it automatically discards the oldest element when you append a new one beyond `maxlen`.  
So memory is trimmed *on-the-fly* without us writing extra pruning code.

### 3.a) Read path (get)

```python
async def get(self, convo_id: str) -> List[Turn]:
    await self._maybe_prune(convo_id)
    dq = self._store.get(convo_id)
    return list(dq) if dq else []
```


**Explanation:**
- Before returning history, `_maybe_prune` checks TTL. If the conversation is expired, it's deleted.
- Then we look up the deque for the conversation_id.
- We return a **list copy** of the deque. This is critical: callers can’t accidentally mutate the internal store.

So the `get()` method always returns the freshest safe snapshot of the conversation.

### 3.b) Write path (append)

```python
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
```


**Explanation:**
- Acquire lock to avoid race conditions.
- If no deque exists for this conversation, create one.
- Append a new turn (role=user or assistant).
- Update last-touched timestamp.
- If total conversations exceed global cap (`_max_convos`), evict the oldest one based on `_last`.

This guarantees **bounded memory usage** regardless of how many clients connect.

### 3.c) TTL prune (_maybe_prune)

```python
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


**Explanation:**
- If TTL is 0, skip pruning (disabled).
- Otherwise, check if the conversation's last activity is older than TTL.
- If yes, delete it from both `_store` and `_last`.

This ensures stale conversations don’t linger forever, keeping memory clean.

## 4) Prompt assembly with history: agents/base.py

```python
def _render_history(history):
    parts = []
    for turn in history:
        role = turn.get("role","user")
        content = turn.get("content","")
        if role == "assistant":
            parts.append(f"<assistant>\n{content}\n</assistant>")
        else:
            parts.append(f"<user>\n{content}\n</user>")
    return "\n".join(parts)
```

```python
def build_prompt(system, user, history=None):
    hist = _render_history(history or [])
    if hist:
        return f"<system>\n{system}\n</system>\n\n{hist}\n\n<user>\n{user}\n</user>"
    else:
        return f"<system>\n{system}\n</system>\n\n<user>\n{user}\n</user>"
```


**Explanation:**
- `_render_history`: converts each past turn into either `<user>` or `<assistant>` XML-style tags.
- `build_prompt`: inserts system instructions, followed by rendered history, then the new user message.

This structure helps the model "see" the dialogue flow while respecting its context budget.  
Oldest turns are naturally dropped because of deque limits.

## 5) Endpoint flow: app.py (/chat)

```python
class ChatRequest(BaseModel):
    message: str
    agent: str = "general"
    stream: bool = False
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
```

```python
@app.post("/chat")
async def chat(req: ChatRequest, request: Request):
    convo_id = req.conversation_id or str(uuid4())
    history = []
    if config.ENABLE_MEMORY:
        history = await _memory.get(convo_id)
    system = load_system_prompt()
    prompt = build_prompt(system, req.message, history)
    ...
```


**Flow explained:**
1. **Conversation ID**: If absent, generate a new UUID.
2. **Load memory**: If enabled, get recent turns for that convo_id.
3. **Build prompt**: System + history + current user message.
4. **Non-stream**: Call provider, get full reply, return JSON, append user & assistant turns.
5. **Stream**: Call provider with stream=True, yield chunks as they arrive. After completion (or disconnect), append turns to memory.
6. **Return**: For stream, attach `X-Conversation-Id` header. For non-stream, include in JSON body.

Thus, memory is always updated after each interaction so continuity works.

## 6) Why these choices?


- **Bounded memory**: prevents RAM/token blowup on Pi.
- **Deque**: automatic trimming of old turns.
- **TTL + LRU**: ensures memory stays clean and predictable.
- **Prompt format**: efficient, keeps dialogue coherent.
- **Locking**: ensures thread safety even if multiple requests overlap.

## 7) Testing tips


- **Non-stream continuity**: Start a conversation, reuse conversation_id, confirm context is remembered.
- **Stream continuity**: Use `curl -i` to capture `X-Conversation-Id`, reuse it.
- **TTL test**: Set MEMORY_TTL_MIN=1, wait >1 minute, check that conversation is reset.
- **LRU test**: Set MEMORY_MAX_CONVERSATIONS=2, open 3 conversations, confirm oldest one is evicted.
