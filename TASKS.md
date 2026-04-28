# AgentForMc-Reranker Task Board

## Goal

Provide a lightweight standalone reranker middleware for AgentForMc so users can enable reranking by running this service, without loading the heavy BCE model inside the main backend process.

## Current State

- Standalone Python package and gRPC service are in place.
- Config and env loading are in place.
- Bearer-token auth is enforced for `Rerank`.
- `Health` and `Rerank` RPC tests pass.
- Backend integration has been implemented in `F:\AgentForMc`.
- Local repo `.venv` still needs dependencies installed before it can run tests independently.

## Phase 0: Documentation Baseline

- [x] Create `AGENTS.md`.
- [x] Create `MEMORY.md`.
- [x] Create `TASKS.md`.

## Phase 1: Middleware Runtime

- [x] Replace starter `main.py` with a real service entrypoint.
- [x] Add package layout under `agent_for_mc_reranker/`.
- [x] Add config loading from `config.toml` and `.env`.
- [x] Add BCE model wrapper.
- [x] Add gRPC server startup and self-check.
- [x] Add `.env.example`, `.gitignore`, `requirements.txt`, and `README.md`.
- [ ] Install `requirements.txt` into the repo-local `.venv`.
- [ ] Run the middleware tests using the repo-local `.venv`.

## Phase 2: gRPC Contract

- [x] Define standalone `reranker.proto`.
- [x] Generate Python protobuf and gRPC stubs.
- [x] Add `Health` RPC.
- [x] Add `Rerank` RPC.
- [x] Require Bearer token on `Rerank`.
- [x] Preserve stable tie ordering.
- [ ] Add a small manual client or smoke script for local deployment checks.

## Phase 3: Backend Integration

- [x] Mirror `reranker.proto` in `F:\AgentForMc`.
- [x] Add backend `GrpcRerankerClient`.
- [x] Add backend reranker host/port/timeout/token config.
- [x] Remove backend direct `BCEmbedding` runtime dependency.
- [x] Preserve backend fallback when reranker is unavailable.
- [x] Verify backend tests pass.
- [ ] Run a manual end-to-end Ask flow with both services running.

## Phase 4: Packaging And Operations

- [ ] Decide whether this service needs PyInstaller packaging like AgentForMc.
- [ ] Add release packaging if needed.
- [ ] Document deployment examples for same-machine and remote-machine setups.
- [ ] Decide whether `Health` should require auth in production.
- [ ] Add logging and optional observability if operational needs justify it.

## Verification Commands

Preferred once repo-local dependencies are installed:

```powershell
F:\AgentForMc-Reranker\.venv\Scripts\python.exe -m pytest
```

Current verified fallback command:

```powershell
F:\AgentForMc\.venv\Scripts\python.exe -m pytest
```

Self-check:

```powershell
$env:RAG_RERANKER_GRPC_AUTH_TOKEN="change_me"
F:\AgentForMc-Reranker\.venv\Scripts\python.exe main.py --self-check
```

## Open Blockers

- Repo-local `.venv` does not yet have project dependencies installed.
- Manual end-to-end verification with a live AgentForMc process has not been run.
- Packaging and production deployment shape are not decided.
