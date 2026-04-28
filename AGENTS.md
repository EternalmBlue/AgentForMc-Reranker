# AgentForMc-Reranker Working Guide

## Project Role

This repository is the standalone reranker middleware for `F:\AgentForMc`.

Its job is to run the heavy BCE reranker model in a separate process and expose a narrow gRPC API that the backend can call when reranking is enabled. The main backend remains responsible for QA, retrieval, BM25/vector fusion, DeepAgent orchestration, Minecraft config ingestion, and answer generation.

## Required Reading Order

Before making non-trivial changes in this repo:

1. Read `TASKS.md` for current work and blockers.
2. Read `MEMORY.md` for stable project facts and integration assumptions.
3. If the work is a non-trivial bug fix or implementation, run `$bug-memory-loop` preflight recall for the current task and touched paths.

After fixing a meaningful bug with a clear root cause, capture a repo-scoped lesson with `$bug-memory-loop` unless the prevention rule is clearly global.

## Hard Boundaries

- Do not modify `F:\Agent4Minecraft` unless the user explicitly asks for plugin-side edits.
- Do not modify `F:\AgentForMc` unless the task explicitly requires backend integration changes.
- Do not put QA, retrieval, vector-store, BM25, DeepAgent, or Minecraft sync logic in this repo.
- Do not add REST or WebSocket fallbacks for reranking unless the user explicitly changes the contract.
- Do not bypass gRPC authorization. Rerank calls must require `authorization: Bearer <RAG_RERANKER_GRPC_AUTH_TOKEN>`.
- Do not hardcode tokens, backend URLs, model cache roots, or deployment-specific filesystem paths in code.
- Do not commit `.env`, model caches, virtualenvs, pytest caches, or generated runtime data.

## Expected Responsibilities

- Load and warm the BCE reranker model.
- Expose a small gRPC service for health checks and reranking.
- Score `(query, document text)` pairs with `BCEmbedding.RerankerModel.compute_score`.
- Sort by score descending and preserve original order for ties.
- Return ranked document indexes, document IDs, and scores.
- Keep model, bind address, timeout, worker count, and cache path configurable.
- Keep auth secrets in environment variables and non-sensitive operational settings in `config.toml`.

## gRPC Contract

Proto source of truth in this repo:

- `agent_for_mc_reranker/interfaces/grpc/reranker.proto`

Current RPCs:

- `Health(HealthRequest) -> HealthResponse`
- `Rerank(RerankRequest) -> RerankResponse`

Backend mirror:

- `F:\AgentForMc\agent_for_mc\interfaces\grpc\reranker.proto`

When changing the reranker proto, update both repos' proto files, regenerate Python stubs, and update tests on both sides.

## Recommended Code Layout

- `agent_for_mc_reranker/config.py` for config and env loading.
- `agent_for_mc_reranker/model.py` for local BCE model loading and scoring.
- `agent_for_mc_reranker/service.py` for gRPC servicer behavior and auth checks.
- `agent_for_mc_reranker/server.py` for service startup and CLI/self-check behavior.
- `agent_for_mc_reranker/interfaces/grpc/` for proto and generated gRPC code.
- `tests/` for config and in-process gRPC tests.

## Quality Bar

- Add or update tests for config loading, auth metadata, empty requests, sorting stability, and error mapping when behavior changes.
- Prefer in-process gRPC tests over hand-written network mocks for transport behavior.
- Keep generated protobuf files aligned with `grpcio-tools==1.71.0`.
- Run the test suite before handing off changes.

## Current Commands

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run tests:

```powershell
python -m pytest
```

Run self-check:

```powershell
$env:RAG_RERANKER_GRPC_AUTH_TOKEN="change_me"
python main.py --self-check
```

Start service:

```powershell
$env:RAG_RERANKER_GRPC_AUTH_TOKEN="change_me"
python main.py
```

## Current State Reminder

As of `2026-04-28`, this repository contains the first standalone reranker middleware implementation:

- Python package `agent_for_mc_reranker`
- gRPC proto and generated Python stubs
- Bearer-token protected `Rerank`
- unauthenticated `Health`
- BCE model wrapper
- config/env loading
- initial unit and in-process gRPC tests

The backend integration lives in `F:\AgentForMc` through its remote reranker client and fallback retrieval behavior.
