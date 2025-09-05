# Pi FastAPI Agent Server

Lightweight multi-agent server built on **FastAPI**, designed to run on Raspberry Pi.  
Current version: 0.3.0 (**Phase 2**) — single agent, Ollama provider, stream and non-stream `/chat`, short conversation memory.

---

## Docs Contents

  ## Contents
  - [01. app.py](/docs/app_py.md)
  - [02. agents/*](/docs/agents.md)
  - [03. providers/*](/docs/providers.md)
  - [04. config](/docs/config.md)
  - [05. memory](/docs/memory.md)
  - [06. Streaming](/docs/streaming.md)





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
  agents_base.py            # prompt builder
  agents_general.py         # general agent system prompt loader
providers/
  providers_base.py            # provider contract + ProviderError
  providers_ollama.py          # Ollama provider implementation (non-stream)
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






