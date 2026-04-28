# AgentForMc-Reranker Memory

## Stable Facts

- Created as a standalone reranker middleware on `2026-04-28`.
- Repository path: `F:\AgentForMc-Reranker`.
- Backend repository path: `F:\AgentForMc`.
- Minecraft plugin repository path: `F:\Agent4Minecraft`.
- This repo is a middleware service, not the main backend brain and not a Minecraft plugin.

## Integration Facts

- Default reranker gRPC bind address is `127.0.0.1:50052`.
- Backend-to-reranker auth uses `authorization: Bearer <RAG_RERANKER_GRPC_AUTH_TOKEN>`.
- The backend enables remote reranking with:

```toml
[reranker]
enabled = true
host = "127.0.0.1"
port = 50052
timeout_seconds = 10
```

- If the reranker middleware is unavailable, the backend should degrade to BM25/vector fusion instead of failing the Ask request.
- The Minecraft plugin gRPC contract is unchanged by this repo.

## Contract Facts

- Proto file: `agent_for_mc_reranker/interfaces/grpc/reranker.proto`.
- Backend mirror: `F:\AgentForMc\agent_for_mc\interfaces\grpc\reranker.proto`.
- RPCs:
  - `Health(HealthRequest) -> HealthResponse`
  - `Rerank(RerankRequest) -> RerankResponse`
- `RerankRequest` carries `request_id`, `query`, repeated `{index, document_id, text}`, and optional `top_k`.
- `RerankResponse` returns ranked `{index, document_id, score}` records.
- Sorting rule: score descending, original input order preserved for ties.

## Runtime Facts

- Default model is `maidalun1020/bce-reranker-base_v1`.
- Local model implementation uses `BCEmbedding.RerankerModel.compute_score`.
- Model cache defaults to `.cache/models`.
- Secrets belong in `.env` or environment variables.
- Non-sensitive settings belong in `config.toml`.
- `.env`, `.cache/`, `.venv/`, `__pycache__/`, and pytest caches should not be committed.

## Verification Facts

- On `2026-04-28`, the reranker test suite passed using:

```powershell
F:\AgentForMc\.venv\Scripts\python.exe -m pytest
```

- The repo-local `.venv` existed but did not yet have `grpc` or `pytest` installed at that time.
- Self-check passed with:

```powershell
$env:RAG_RERANKER_GRPC_AUTH_TOKEN='test-token'
F:\AgentForMc\.venv\Scripts\python.exe main.py --self-check
```

## Memory Rule

Keep this file for stable project facts, confirmed assumptions, and integration truths.

Do not store transient todos here. Use `TASKS.md` for execution work.
