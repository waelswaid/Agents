
```markdown
# Pi FastAPI Agent Server

Lightweight multi-agent server built on **FastAPI**, designed to run on Raspberry Pi.  
Current version: **Phase 1** — single agent, Ollama provider, non-stream `/chat`.

---

## Features (current version)

- ✅ **Health check** endpoint (`/health`)
- ✅ **List available agents** (`/agents`)
- ✅ **Chat endpoint** (`/chat`) with:
  - Input validation via **Pydantic**
  - System + user prompt composition
  - Provider abstraction (Ollama implemented)
  - Configurable model, context length, max tokens, temperature
- ✅ **Environment-based config** (`.env` or defaults)
- ✅ **Error handling** (`ProviderError` → 502; validation errors → 422)

---


```

## Project Structure


agents/
--base.py            # prompt builder
--general.py         # general agent system prompt loader
providers/
--base.py            # provider contract + ProviderError
--ollama.py          # Ollama provider implementation (non-stream)
prompts/
--general_system.txt # system prompt for the general agent
utils/
--config.py          # centralized configuration loader
--app.py               # FastAPI entry point (endpoints & routing)
.env                 # environment variables (not committed)
.gitignore
requirements.txt
README.md

````

```


---

## Endpoints

### `GET /health`
Returns server health.

**Response**
```json
{ "status": "ok" }
````

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
PROVIDER=ollama
OLLAMA_MODEL_GENERAL=qwen2.5:3b-instruct
OLLAMA_HOST=http://127.0.0.1:11434
CTX_TOKENS=2048
MAX_TOKENS=200
TEMPERATURE=0.7
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

curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"say hello","agent":"general","stream":false}'
```

---

## Limitations (Phase 1)

* Only one agent (`general`)
* Only one provider (Ollama, non-stream mode)
* No conversation memory
* No streaming responses
* No rate limiting or security layer
* Logging is minimal

---

## Next Steps (Planned)

* Phase 2: Streaming responses + short-term conversation memory
* Phase 3: Tool calling with a safe allowlist
* Phase 4: Add OpenAI provider (switchable backends)
* Phase 5: Security hardening (rate limits, CORS, API key)
* Phase 6: SQLite persistence & admin ops
* Phase 7: Tiny RAG starter for local docs

---
