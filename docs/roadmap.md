
# Pi FastAPI Agent Server — Roadmap Beyond Phase 2

**Deep explanation of Phases 3–7 and Final Capabilities**  
Generated: 2025-09-03 02:01

---

## SCOPE
This document provides a deep explanation of each planned phase after Phase 2.  
It clarifies the rationale, expected code changes, design constraints, and testing methods.  
At the end, it summarizes the complete project vision: what the server will be able to do, what types of agents it can run, and what tools are integrated safely.

---

## PHASE 3 — Tools & Allowlist

**Goal:**  
Give agents safe, controlled capabilities (math, time, search) without exposing the Pi to arbitrary code execution.

### Why:
- Models excel at reasoning but fail at exact math or structured external calls.
- A tool protocol lets the agent “call” a sandboxed function that we implement.
- Security: strict allowlist ensures only safe functions with capped inputs.

### Implementation:
- **Protocol:** model outputs a line like: `CALL_TOOL: calc | 12*(7+1)`.
- **Parser:** validate tool name ∈ allowlist, validate input length, regex to enforce digits/operators only.
- **Tools implemented:**
  - `calc`: safe arithmetic (with restricted eval or small parser).
  - `now`: returns ISO8601 timestamp.
- `agents/code_math.py`: system prompt instructs model on tool usage, `allowlist = ["calc","now"]`.

### Testing:
- `/chat agent=code, message="12*(7+1)"` → server intercepts `CALL_TOOL`, runs calc, injects result back to model context, returns final answer.
- Malformed tool call → rejected safely; agent receives error message and continues.

---

## PHASE 4 — Multi-Provider Abstraction (e.g., OpenAI)

**Goal:**  
Allow the same API to use different model backends (Ollama local, OpenAI cloud).

### Why:
- **Flexibility:** run locally on Pi or scale to OpenAI/Groq/DeepSeek in the cloud.
- **Reliability:** fallback providers when one fails.

### Implementation:
- `providers/openai.py`: implement `generate()` with non-stream + stream (using openai SDK or httpx).
- `config.PROVIDER = "ollama" | "openai"`; load appropriate generate function via mapping, not if/else.
- `/models` endpoint: list active provider + available models.

### Testing:
- Flip PROVIDER=openai in `.env`, run server; `/chat` works unchanged.
- Logs show provider and model used.

---

## PHASE 5 — Security & Hygiene

**Goal:**  
Prepare the API for exposure beyond localhost.

### Why:
- Streaming + tools increase attack surface.
- Protect Pi from abuse and prevent runaway resource usage.

### Implementation:
- Rate limiting (e.g., 30 req/min per IP, in-memory or Redis).
- Request size limits (max 64KB body, max 4000 chars message).
- CORS: allow only specific origins (phone/web client).
- Optional API key header (`X-API-KEY`).
- Logging: structured JSON with request id, agent, provider, latency, tokens.

### Testing:
- Exceed rate limit → 429 Too Many Requests.
- Oversized message → 413 Payload Too Large.
- CORS rejects unknown origins.

---

## PHASE 6 — Persistence & Admin Ops

**Goal:**  
Support persisting conversations beyond memory and add observability.

### Why:
- Restart-safe conversations.
- Debugging and analytics.

### Implementation:
- SQLite (lightweight) with tables: `conversations(id, created_at)`, `messages(conversation_id, role, content, ts)`.
- MemoryStore swapped with DB-backed version if `PERSIST_MEMORY=true`.
- **Admin endpoints:**
  - `/admin/export?conversation_id=...` → JSON dump of conversation.
  - `/health` → extended to include DB + provider status.

### Testing:
- Restart server, reuse conversation_id → history still present.
- Export a conversation and inspect JSON.

---

## PHASE 7 — Retrieval-Augmented Generation (RAG)

**Goal:**  
Let agents use local docs safely.

### Why:
- Ground model answers in specific whitelisted knowledge (docs folder).
- Supports gym owners, trainers, or small businesses storing their own FAQ/data.

### Implementation:
- `rag_docs/` folder, only whitelisted files processed.
- Simple search (keyword or TF-IDF); optionally small embeddings later.
- **Tool:** `search_docs(query)` returns top-k snippets.
- **Agent:** RAG agent system prompt instructs model to call `search_docs` when relevant.

### Testing:
- Ask a question present in `rag_docs`; agent calls `search_docs`, receives snippet, includes snippet id in answer.
- Non-relevant query → falls back to general answer.

---

## FINAL CAPABILITIES SUMMARY

Once all phases are complete, the Pi FastAPI Agent Server will provide:

### 1. Multi-agent architecture:
- General agent — conversational, helpful, concise.
- Code/Math agent — with calc and time tools, accurate math.
- RAG agent — answers grounded in local docs.
- Any future agents — defined by prompt + allowlist of tools.

### 2. Multi-provider support:
- Ollama local models (Pi-compatible small LLMs like qwen2.5-mini).
- OpenAI / cloud LLMs (GPT-4o, GPT-5 when available).

### 3. Tools:
- `calc`, `now` (Phase 3).
- `search_docs` (Phase 7).
- Extensible: add weather, db_query, etc., by appending to allowlist.

### 4. Security posture:
- Rate limiting, body size caps, CORS, API key (Phase 5).

### 5. Persistence & observability:
- SQLite persistence, `/admin/export`, extended `/health` (Phase 6).
- Structured logging.

### 6. UX features:
- Streaming tokens with fast first-byte (Phase 2).
- Short-term and persistent memory (Phases 2 & 6).

---

## ULTIMATE VALUE
The project evolves from a Pi-local demo into a portable multi-agent framework:
- Runs lightweight on a Pi.
- Scales to cloud with OpenAI.
- Supports safe tool use, memory, and retrieval.
 

**Ready for cloud deployment.**