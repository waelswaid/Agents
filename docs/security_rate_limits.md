# 13. Security & Rate Limits (Roadmap)

## API Keys
- Header: `x-api-key: <key>`
- Middleware checks key → sets `request.state.tenant`.
- Per-tenant quotas & usage counters.

## CORS
- Allow only your frontend origins.
- Deny `*` in production.

## Rate Limiting
- `slowapi` with per-IP or per-key buckets (e.g., 60 req/min).
- Return **429** with `Retry-After`.

## Request Limits
- Max JSON size (e.g., 64 KB) — avoid huge prompts.
- Timeouts with sane defaults.

## Auditing
- Log auth failures and throttling events.
