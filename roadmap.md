# Roadmap: Pi Agent Server → AI Dev Agent Platform

This roadmap shows how we will evolve the Pi Agent Server into a **full platform that rents AI developer agents**.  
We start by using **LangChain only inside the agent layer** to quickly deliver a working agent + demo.  
As we progress, LangChain will be **gradually replaced by fully custom code** while keeping the API and external behavior stable.

---

## Core Principles

- **Stable interfaces** – `/chat` stays backward-compatible throughout.  
- **Local-first safety** – all tools start **read-only**, with strict path guards, timeouts, and output caps.  
- **Layered design** – transport, provider, memory, and governance remain **custom** and separate from agent orchestration.  
- **Easy swap-out** – LangChain is confined to one internal interface (`AgentRunner`) so replacing it later is seamless.

---

## Architecture Overview
```
agents/
│
├── runner.py # Stable interface: AgentRunner base class
├── runner_lc.py # TEMP LangChain-based implementation
├── runner_custom.py # FUTURE fully custom implementation
│
├── tools/ # Pure Python, read-only tools
│ ├── fs_read.py # grep, read_text, outline_python
│ ├── analysis.py # later: pylint, ruff, bandit
│ ├── tests.py # later: pytest discovery/runner
│ └── patch.py # later: diff generation
│
└── ...
```

**FastAPI + Provider + Memory**  
These stay completely **custom**:
- `/chat` endpoint and streaming logic
- Provider modules (`providers_ollama.py`, future `providers_openai.py`)
- Short-term memory (`MemoryStore`)
- JSONL logs, safety checks, governance

---

## Phase Plan

### **Phase 0 – Skeleton Setup (no behavior change)**
- Create folder structure: `tools/`, `agents/runner.py`, `agents/runner_lc.py`.  
- Keep `/chat` identical, just allow `"agent":"dev_generalist"`.  
- Implement empty stubs for tools (`fs_read.py` functions with strict path guards).  
- **Acceptance:** old API requests behave exactly as before.

---

### **Phase 1 – LangChain-Backed Developer Agent (Demo Ready)**
Goal: a **working dev agent** that can read code safely and answer with **citations**.

**LangChain usage (temporary):**
- Use LangChain **only inside `runner_lc.py`**:
  - Agent planning and orchestration (`grep` → `read_text` → synthesize answer).
  - Wrap tools as `StructuredTool` for validation.
  - Optional output parsing (`PydanticOutputParser`) for structured formats.
  - LangChain callbacks for temporary tracing.

**Custom remains:**
- `/chat` transport, streaming, partial-save, and error handling.
- Provider and memory.
- JSONL logging (source of truth).

**Acceptance Criteria:**
- The agent can:
  - Search the repo (`grep`) for patterns.
  - Read targeted files (`read_text`).
  - Answer questions with precise `file:path#line_start-line_end` citations.
- API behavior identical to general agent, just smarter responses.

---

### **Phase 2 – Static Analysis & Quality Signals**
Add **read-only analyzers**:
- `pylint`, `ruff`, `bandit` run in sandboxed subprocesses with strict timeouts.
- Summarize top 5 issues per tool with file/line and recommended fix.
- Integrate into the LangChain planning step for now.

---

### **Phase 3 – Test Discovery & Runner**
- Detect tests automatically.
- Run tests in isolated subprocesses (no network, strict timeouts).
- Parse results and explain failures in structured format.
- Continue to use LangChain orchestration temporarily.

---

### **Phase 4 – Patch Proposal (Human-in-the-Loop)**
- Generate **unified diff proposals** for fixes (no writes yet).
- Return diffs to the user for review.
- Actual writes require explicit human approval in Phase 6.

---

### **Phase 5 – Long-Term Memory (RAG)**
- Add embeddings and vector search for historical conversations and code context.
- **LangChain retrievers** can be used temporarily, but all storage and safety limits remain custom.

---

### **Phase 6 – Observability & Governance**
- Add config knobs:
  - `AGENT_MAX_STEPS`
  - `TOOL_TIMEOUT_DEFAULT`
  - `WRITE_GUARD_REQUIRE_CONFIRM`
- Enhanced logs:
  - Request IDs
  - Per-tool JSONL logs
  - Token counts and cost tracking (for API LLMs)

---

### **Phase 7 – Safe Write Operations**
- Add `/apply_patch` endpoint with **`ALLOW_WRITE=false` by default**.
- Human approval or explicit config required to allow writes.

---

### **Phase 8 – Multi-Agent Orchestration**
- Introduce role-based agents (architect, coder, tester, reviewer).
- Custom orchestrator (`agents/runner_custom.py` or `orchestration/router.py`) replaces LangChain entirely.
- Keep `/chat` as default single-agent path.
- Add `/orchestrate` for advanced workflows.

---

## LangChain → Custom Transition Plan

| Area | LangChain Now | Custom Later |
|------|---------------|--------------|
| Agent orchestration | LCEL graph for planning & tool use | Your own deterministic `AgentRunner` |
| Tool wrapping | `StructuredTool` | Direct calls to pure functions |
| Output parsing | LC output parsers | Pydantic/JSON schema validation |
| Observability | LC callbacks | Pure custom JSONL + metrics |
| Retrieval (RAG) | LC retrievers | Your vector DB client |

---

## Final State

- **Fully custom platform** for renting AI developer agents.
- LangChain completely removed.
- Clean, well-tested, and optimized codebase with strict safety and governance.

---

## Immediate Next Steps

1. Implement Phase 0 skeleton:
   - Add empty tool files and `runner_lc.py`.
   - Expand `ALLOWED_AGENTS` to include `"dev_generalist"`.
2. Build Phase 1 LangChain-backed dev agent:
   - Implement `grep`, `read_text`, and `outline_python` with strict read-only guards.
   - Wrap them in LangChain `StructuredTool`.
   - Build a simple LCEL chain for plan → tool → answer.
3. Add JSONL logging for every step, even if LangChain callbacks are also active.
4. Validate with test prompts:
   - No tools → direct model answer.
   - Code questions → tools invoked before model.
   - Correct citations included in answers.

---

By following this roadmap, you will:
- Quickly deliver a **functioning demo** for investors or early customers.
- Avoid lock-in by isolating LangChain inside one interface.
- Smoothly transition to a **fully custom, scalable platform** as your product grows.
