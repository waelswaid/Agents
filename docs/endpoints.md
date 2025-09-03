# 02. API Endpoints

## `GET /health`
**Purpose:** liveness probe.
**Response:**
```json
{"status": "ok"}
```

## `GET /agents`
**Purpose:** list supported agents.
**Response:**
```json
{"agents": ["general"]}
```

## `POST /chat` — Non-Streaming
**Request:**
```json
{
  "message": "say hello",
  "agent": "general",
  "stream": false,
  "conversation_id": "optional-uuid"
}
```
**Response (200 OK):**
```json
{
  "reply": "Hello! ...",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "model": "qwen2.5:3b-instruct",
  "provider": "ollama"
}
```

## `POST /chat` — Streaming
**Request:** (same fields, with `"stream": true`)
**Response headers:**
- `Content-Type: text/plain; charset=utf-8`
- `X-Conversation-Id: <uuid>`

**Response body:** token chunks as they arrive, e.g.:
```
Hel
lo, 
I a
m r
...
```

**Errors:**
- `422` — validation errors (see Pydantic section).
- `502` — provider failure (maps `ProviderError`).

**Notes:**
- For browser UX, consider adding SSE endpoint later.
- Always echo the `X-Conversation-Id` so clients can chain turns.
