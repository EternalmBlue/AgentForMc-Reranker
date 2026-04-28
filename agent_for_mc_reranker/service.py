from __future__ import annotations

from typing import Protocol

import grpc

from agent_for_mc_reranker.interfaces.grpc import reranker_pb2, reranker_pb2_grpc


class ScoreModel(Protocol):
    model_name_or_path: str

    def warmup(self) -> None:
        ...

    def compute_scores(self, query: str, passages: list[str]) -> list[float]:
        ...


class RerankerService(reranker_pb2_grpc.RerankerServiceServicer):
    def __init__(self, *, ranker: ScoreModel, auth_token: str):
        self._ranker = ranker
        self._auth_token = auth_token.strip()

    def Health(self, request, context):
        return reranker_pb2.HealthResponse(
            ready=True,
            model_name=self._ranker.model_name_or_path,
            message="reranker ready",
        )

    def Rerank(self, request, context):
        self._require_authorization(context)
        documents = list(request.documents)
        if not documents:
            return reranker_pb2.RerankResponse(request_id=request.request_id)

        passages = [document.text for document in documents]
        try:
            scores = self._ranker.compute_scores(request.query, passages)
        except Exception as exc:  # pragma: no cover - external model failure
            context.abort(grpc.StatusCode.INTERNAL, f"reranker model failed: {exc}")

        if len(scores) != len(documents):
            context.abort(
                grpc.StatusCode.INTERNAL,
                "reranker returned a score count that does not match documents",
            )

        scored_documents = [
            (position, document, float(score))
            for position, (document, score) in enumerate(zip(documents, scores))
        ]
        scored_documents.sort(key=lambda item: (-item[2], item[0]))
        if request.top_k > 0:
            scored_documents = scored_documents[: request.top_k]

        return reranker_pb2.RerankResponse(
            request_id=request.request_id,
            results=[
                reranker_pb2.RankedDocument(
                    index=document.index,
                    document_id=document.document_id,
                    score=score,
                )
                for _, document, score in scored_documents
            ],
        )

    def _require_authorization(self, context) -> None:
        metadata = dict(context.invocation_metadata())
        authorization = metadata.get("authorization", "")
        if not authorization:
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "missing authorization metadata",
            )
        if not authorization.startswith("Bearer "):
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "authorization must use a Bearer token",
            )
        token = authorization[len("Bearer ") :].strip()
        if token != self._auth_token:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "invalid authentication token")
