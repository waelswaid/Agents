# Pi FastAPI Agent Server

Lightweight multi-agent server built on **FastAPI**, designed to run on Raspberry Pi.  
Current version: 0.3.0 (**Phase 2**) — single agent, Ollama provider, stream and non-stream `/chat`, short conversation memory.

---

## Docs Contents

  ## Contents
  - [00. Current phase report](/docs/phase2_report.md)
  - [01. Architecture](/docs/architecture.md)
  - [02. app.py](/docs/app_py.md)
  - [03. agents/*](/docs/agents.md)
  - [04. providers/*](/docs/providers.md)
  - [05. config](/docs/config.md)
  - [06. memory](/docs/memory.md)
  - [07. Streaming](/docs/streaming.md)
  - [08. Roadmap](/docs/roadmap.md)





## Features

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

## Run the Server and stream tests
```bash
./run_tests.sh
```

---

## Limitations (Phase 2)

- Only one agent (`general`)
- Only one provider (Ollama)
- No rate limiting or security layer
- Logging is minimal

---






