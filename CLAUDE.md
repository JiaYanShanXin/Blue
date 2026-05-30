# CLAUDE.md

Guidance for AI assistants working in this repository. The layout below follows the same eight-layer story as `readme.md` / `AGENTS.md` so navigation stays consistent.

---

### 1. `chore: bootstrap repo and dependencies`

**Meaning**: Establish the engineering boundary first—how to install, what to ignore, where env secrets live, and any platform/deploy scripts.  
**Narrative role**: No product logic yet; only collaboration and runnability.

**In this repo**: `requirements.txt`, `pyproject.toml`, `frontend/package.json`, `.env.example`, `scripts/`, `.coze`, top-level docs.

---

### 2. `feat(core): config, logging, state, llm, and routing`

**Meaning**: Backend “engine room”: configuration, logging, shared `AgentState`, multi-provider LLM wiring, and conditional edges after Planner/Coder.  
**Narrative role**: Everything else hangs off this layer.

**Entry points**: `src/core/config.py`, `logger.py`, `state.py`, `llm_engine.py`, `routing.py`.

---

### 3. `feat(tools): file tools for planner and coder`

**Meaning**: How agents touch disk—read/write/edit/backup/list, plus the Planner-facing subset.  
**Narrative role**: Bridges model output to the real filesystem.

**Entry point**: `src/tools/file_tools.py`.

---

### 4. `feat(agents): planner, coder, sandbox, reviewer`

**Meaning**: The four behavioral nodes: plan, edit code, run tests in Docker, diagnose failures.  
**Narrative role**: All multi-agent behavior lives here before final graph wiring.

**Entry points**: `src/agents/Planner.py`, `Coder.py`, `Sandbox.py`, `Reviewer.py`.

---

### 5. `feat(graph): LangGraph workflow entrypoint`

**Meaning**: `run.py` composes nodes, tool nodes, and routers into an executable `StateGraph` (CLI / programmatic entry).  
**Narrative role**: The workflow runs end-to-end, not as four loose files.

**Entry point**: `run.py`.

---

### 6. `feat(context): context manager, repo map, metrics, recovery`

**Meaning**: Scale and reliability—context compression, AST repo map for large files, metrics, circuit-breaker snapshots.  
**Narrative role**: Moves the project from demo to observable and recoverable runs.

**Entry points**: `src/core/context_manager.py`, `repo_map.py`, `metrics.py`, `recovery.py`.

---

### 7. `feat(server+api+frontend): FastAPI SSE, models, and React UI`

**Meaning**: Expose the graph over HTTP + SSE; Pydantic models for I/O; React UI for chat, metrics, files, config.  
**Narrative role**: Product-shaped web app on top of the graph.

**Entry points**: `api_server.py`, `src/api/models.py`, `frontend/`.

---

### 8. `test+ci: pytest coverage and GitHub Actions`

**Meaning**: Automated tests lock behavior; CI runs them on push/PR.  
**Narrative role**: Quality gates in later iteration.

**In this repo**: Run `pytest` locally; coverage thresholds live in `pyproject.toml`. Host-specific CI is not checked in here.

---

## Development commands

```bash
pip install -r requirements.txt
pytest
pytest tests/test_file_tools.py
python api_server.py
python run.py
pip install -e .
OurAI
```

Frontend dev:

```bash
cd frontend
npm install
npm run dev
```

Docker Desktop must be running for the sandbox.

## Configuration

- Env file: `src/core/.env` (not committed); template: `.env.example`.
- Providers: OpenAI, Anthropic, Ollama, DeepSeek keys/URLs as documented in `.env.example`.

## Architecture notes

- **Workflow** (`run.py`): `route_after_planner` → tools or Coder; `route_after_coder` → tools or Sandbox when step cap reached; `route_after_sandbox` → repair loop or snapshot/recovery.
- **Context** (`context_manager.py`): core / working / reference memory with tiktoken when available.
- **Files** (`file_tools.py`): exact → stripped → fuzzy edit matching; large files use AST outline.

## Key file map

| Path | Role |
|------|------|
| `api_server.py` | FastAPI + SSE + static frontend |
| `run.py` | LangGraph builder + CLI |
| `src/api/models.py` | Pydantic API models |
| `src/agents/*.py` | Planner, Coder, Sandbox, Reviewer |
| `src/core/state.py` | `AgentState` + checkpointing |
| `src/core/routing.py` | Router helpers |
| `src/tools/file_tools.py` | File tool implementations |
