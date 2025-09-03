# Pi FastAPI Agent Server

Lightweight multi-agent server built on **FastAPI**, designed to run on Raspberry Pi.  
Current version: **Phase 2** — single agent, Ollama provider, stream/non-stream `/chat`, conversation memory.

---

## Docs Contents

  ## Contents
  - [00. Current phase report](/docs/phase2_report.md)
  - [01. Architecture](/docs/architecture.md)
  - [02. Memory](/docs/short_memory.md)
  - [03. Streaming](/docs/streaming.md)
  - [04. app.py](/docs/app_py.md)
  - [05. Glossary](/docs/glossary.md)
  - [06. Pydantic](/docs/pydantic.md)
  - [07. Decisions](/docs/decisions.md)
  - [08. Roadmap](/docs/roadmap.md)





## Features (current version)

- ✅ **Health check** endpoint (`/health`)
- ✅ **List available agents** (`/agents`)
- ✅ **Chat endpoint** (`/chat`) with:
  - Input validation via **Pydantic**
  - System + user prompt composition
  - Provider abstraction (Ollama implemented)
  - Configurable model, context length, max tokens, temperature
  - Stream and non-stream responses
  - Limited conversational memory
- ✅ **Environment-based config** (`.env` or defaults)
- ✅ **Error handling** (`ProviderError` → 502; validation errors → 422)

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

## Endpoints

### `GET /health`

Returns server health.

**Response**
```json
{ "status": "ok" }
```

### `GET /agents`

Returns available agent names.

**Response**
```json
["general"]
```

### `POST /chat`

Send a prompt to an agent and get a reply.

**Request body**
```json
{
  "message": "say hello",
  "agent": "general",
  "stream": false
}
```

**Response**
```json
{
  "reply": "Hello! (from the model)"
}
```

---

## Configuration

Set in `.env` (or defaults used):

```ini
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

## Requirements

Current `requirements.txt`:

```
fastapi==0.112.2
uvicorn[standard]==0.30.6
httpx==0.27.2
python-dotenv==1.0.1
pydantic==2.8.2
```

Install into a virtualenv:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Run the Server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Test it:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}

curl http://127.0.0.1:8000/agents
# ["general"]

curl -s -X POST http://127.0.0.1:8000/chat   -H "Content-Type: application/json"   -d '{"message":"say hello","agent":"general","stream":false}'

```

Stream Tests:

```bash
curl -N -i -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"count to five","agent":"general","stream":true}'
# note: capture returned conversation id from the "X-Conversation-Id" response header


curl -N -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"and now continue to ten","agent":"general","stream":true,"conversation_id":"<from header>"}'
```


---

## Limitations (Phase 2)

- Only one agent (`general`)
- Only one provider (Ollama)
- No rate limiting or security layer
- Logging is minimal

---

## Next Steps (Planned)

- Phase 3: Tool calling with a safe allowlist
- Phase 4: Add OpenAI provider (switchable backends)
- Phase 5: Security hardening (rate limits, CORS, API key)
- Phase 6: SQLite persistence & admin ops
- Phase 7: Tiny RAG starter for local docs

---





