# 18. Roadmap (Phases 3–6)

**Phase 3 (Platform hardening)**
- Provider registry + OpenAI provider
- API keys + CORS + rate limits
- SSE endpoint; keep chunked
- Config ranges + startup log

**Phase 4 (State & multi-tenancy)**
- SQLite/Postgres conversations
- Optional Redis for short-memory across workers
- Alembic migrations

**Phase 5 (Security & Observability)**
- Structured JSON logs + metrics
- Quotas & usage counters
- Alerts/webhooks

**Phase 6 (Vertical agents)**
- Gym Lead Agent (booking + follow-up)
- SMB Support Agent (returns/FAQ)
