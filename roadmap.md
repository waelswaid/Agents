
# Roadmap to Building a Developer AI Agent

This document provides a concrete, step-by-step roadmap to evolve your current FastAPI project into a **generalist Developer AI Agent**, while keeping every design decision **future-proof** for later scaling into a multi-agent dev team.

---

## Guiding Principles

* **Stable interfaces:** Maintain backward compatibility by adding new optional fields rather than breaking changes.
* **One abstraction per concern:**
  - `Agent` — reasoning + policy
  - `Tool` — capability
  - `Provider` — LLM connection
  - `Memory` — short/long-term data
  - `Orchestrator` — only when multiple agents are added
* **Local-first, safe execution:** All tools are read-only by default. Write access must be explicitly enabled and confirmed by a human.
* **Deterministic logs:** Every tool interaction is logged for replay and auditing.

---

# Phase 0 — Prepare the Skeleton

**Goal:** Introduce project structure without changing behavior.

### Changes

Create the following structure:

```
agents/
  agents_base.py              # Agent protocol with plan() & act()
  agents_general.py           # Current general chat agent (no changes yet)
  dev_generalist.py    # Empty stub for now

tools/
  __init__.py
  fs_read.py           # Repo browsing and search tools
  analysis.py          # Static analysis adapters
  tests.py             # Test runner adapters
  patch.py             # Diff/patch proposer

memory/
  short_term.py        # Existing in-RAM conversation memory
  long_term.py         # Stub for long-term memory

orchestration/
  router.py            # Stub for future multi-agent routing
```

**API compatibility:**  
Keep `POST /chat` unchanged, but add `"agent": "dev_generalist"` as an optional field.

**Acceptance check:**  
`curl` requests to `/chat` should still behave exactly as before.

---

# Phase 1 — Read-only Developer Agent (Repo Understanding)

**Goal:** The agent can read the codebase, answer questions, and provide citations.

### Tools: `tools/fs_read.py`

* `list_repo(root: str) -> dict`
* `read_text(path: str, max_bytes: int) -> str`
* `grep(pattern: str, path: str, ignore: list[str]) -> list`
* `outline_python(path: str) -> list`

Safety: Restrict access to project directory only.

### Agent: `agents/dev_generalist.py`

* Uses your LLM provider to reason.
* Prioritizes targeted reads and outlines over reading entire files.
* Returns citations in the format: `file:path#line_start-line_end`.

### API Example

```json
POST /chat
{
  "agent": "dev_generalist",
  "message": "Explain utils/memory.py get() step by step"
}
```

### Acceptance Checks

* Agent can locate `/chat` definition and explain validation with citations.
* Agent can find provider timeout settings and cite them.

---

# Phase 2 — Static Analysis & Quality Signals

**Goal:** Run static analyzers safely and summarize actionable results.

### Tools: `tools/analysis.py`

* `run_pylint(paths: list[str], max_seconds: int) -> str`
* `run_ruff(paths: list[str], max_seconds: int) -> str`
* `run_bandit(paths: list[str], max_seconds: int) -> str`

Safety: Allowlist binaries, strict timeouts, no external side effects.

### Agent Updates

* Chooses when to run analyzers vs. pure reasoning.
* Summarizes top 5 issues with file locations and suggested fixes.

### Acceptance Checks

* Example prompt: “Audit providers/ollama.py for pitfalls.”
* Timeouts handled gracefully without crashing.

---

# Phase 3 — Test Discovery & Runner

**Goal:** Discover and run tests, then explain failures.

### Tools: `tools/tests.py`

* `discover_pytests(root: str) -> list[str]`
* `run_pytest(args: list[str], max_seconds: int) -> str`

Safety: Sandbox, disable network, enforce strict timeouts.

### Agent Behavior

1. Discover tests.
2. Run tests.
3. Parse failures and explain them.

---

# Phase 4 — Patch Proposal (Human-in-the-Loop)

**Goal:** Agent proposes minimal patches as unified diffs but does not apply them.

### Tools: `tools/patch.py`

* `propose_unified_diff(edits: list) -> str`

Workflow:

1. User asks for a fix.
2. Agent returns a unified diff.
3. Human applies it manually or through a separate endpoint in Phase 6.

---

# Phase 5 — Long-term Project Memory

**Goal:** Persist repo knowledge beyond a single session.

### Tools: `memory/long_term.py`

* `index_files(paths: list[str])`
* `semantic_search(query: str, k: int) -> list`

Use embedding abstraction so local and cloud embeddings can be swapped seamlessly.

### Agent Behavior

* Uses semantic search to find relevant snippets.
* Verifies results with `read_text` before citing.

---

# Phase 6 — Apply Patch Endpoint (Optional)

**Goal:** Enable safe writes with human confirmation.

### API

* `POST /apply_patch`

```json
{
  "diff": "<unified diff>",
  "confirm": true
}
```

Environment flag: `ALLOW_WRITE=false` by default.

---

# Phase 7 — Observability & Governance

**Goal:** Enable tracing and monitoring for debugging and scaling.

### Additions

* Request/response IDs (`X-Request-Id`).
* Tool usage logs (`tools.log.jsonl`).
* Config keys:
  - `AGENT_MAX_STEPS`
  - `TOOL_TIMEOUT_DEFAULT`
  - `WRITE_GUARD_REQUIRE_CONFIRM`

---

# Phase 8 — Multi-Agent Orchestration

**Goal:** Add multi-agent support without breaking existing APIs.

### Additions

* `orchestration/router.py` routes tasks to specialized agents.
* Role agents in `agents/roles/`:
  - `architect.py`
  - `coder.py`
  - `tester.py`
  - `reviewer.py`

`/chat` remains default entrypoint, `/orchestrate` is added for multi-agent workflows.

---

## Locked-in Contracts

### Agent Base

* `plan(user_message, memory, tools)`
* `act(observation)`

### Tool Base

* `run(**kwargs)` with strict validation.

### Memory Base

* `short_term.get()` and `.append()`
* `long_term.search()` and `.upsert()`

---

## Checklist for Developer Agent v1

- [ ] Explain any file/class/function with citations.
- [ ] Search and summarize repo relationships.
- [ ] Run analyzers and present top 5 issues.
- [ ] Run tests and explain failures.
- [ ] Propose diffs without applying them automatically.
- [ ] Log all tool interactions safely.

---

## Upgrade Path to a Multi-Agent Team

* Enable orchestrator and role-based agents.
* Add a shared blackboard for tasks and results.
* Implement policy checks for risky changes.
* Introduce self-play loops for iterative refinement.

---

## Recommended Next Steps

1. Build Phase 0 skeleton.
2. Implement Phase 1 read-only tools.
3. Add Phases 2 and 3 for analyzers and tests.
4. Add Phase 4 diff proposals.
5. Implement long-term memory in Phase 5.
6. Add observability and writes in Phases 6 and 7.
7. Prepare multi-agent setup in Phase 8.
