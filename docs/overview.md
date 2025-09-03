# 00. Overview

The Pi FastAPI Agent Server provides a minimal, **provider-agnostic** runtime for LLM-powered agents:
- **FastAPI** for APIs, validation, and streaming responses.
- **Provider contract** returning either a full string or an **async iterator of tokens**.
- **Short conversation memory** (in-memory with TTL + LRU) injected into prompts.
- Env-based configuration; designed to run on **Raspberry Pi 5** or cloud.

Key principles:
- **Simplicity first**: clean request path, no heavy frameworks.
- **Predictable resources**: bounded memory, timeouts.
- **Swap providers**: Ollama (local) now, OpenAI (cloud) later.
- **Streaming-first UX**: early tokens reduce perceived latency.
