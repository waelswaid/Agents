# 09. Config & .env

Configuration lives in `.env` and is read in `utils/config.py`.

## Keys (examples)
- `PROVIDER=ollama`
- `OLLAMA_MODEL_GENERAL=qwen2.5:3b-instruct`
- `OLLAMA_HOST=http://127.0.0.1:11434`
- `CTX_TOKENS=2048`
- `MAX_TOKENS=200`
- `TEMPERATURE=0.7`
- `ENABLE_MEMORY=true`
- `MEMORY_MAX_TURNS=8`
- `MEMORY_TTL_MIN=60`
- `MEMORY_MAX_CONVERSATIONS=500`

## Recommendations
- Validate ranges (e.g., `0 < TEMPERATURE <= 2`).
- Log the **effective config** at startup (exclude secrets).
- Keep a versioned `.env.example` in the repo; do **not** commit real secrets.
