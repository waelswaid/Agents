# 11. Errors & Logging

## Error Mapping
- Provider issues → raise `ProviderError("...")` → route returns **HTTP 502** with `{"detail":"..."}`.
- Validation → **HTTP 422** automatically from FastAPI/Pydantic.
- Unknown provider → startup fail or **HTTP 500** (prefer fail-fast at startup).

## Logging (Recommended Fields)
- `timestamp`
- `level`
- `request_id` / `conversation_id`
- `agent`, `provider`, `model`
- `latency_first_token_ms`, `duration_ms`, `chunks`
- `status_code`, `error` (if any)

Prefer **structured JSON logs** for searchability and metrics extraction.
