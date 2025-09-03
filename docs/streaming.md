# 04. Streaming (Chunked vs SSE vs WebSocket)

## Current: Chunked `text/plain`
- Implemented via `StreamingResponse(async_generator, media_type="text/plain; charset=utf-8")`.
- Works with `curl`, `fetch`, Python `httpx`, etc.
- Low infra complexity.

### Pros
- Universal; very easy to deploy.
- Fast perceived latency.

### Cons
- No event semantics (`event:` / `data:`) like SSE.
- You handle reconnects yourself.

## SSE (Planned)
- Endpoint returns `text/event-stream` with lines:
  ```
  event: token
  data: Hello

  ```
- Browser `EventSource` is ergonomic and reconnect-friendly.

## WebSocket (Optional)
- Bi-directional, but more infra and client complexity.
- Useful if you later add interactive tools/controls.

## Recommendation
- Keep chunked streaming for generic clients.
- Add `/chat/stream` SSE for web apps.
