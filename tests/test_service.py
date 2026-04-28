from __future__ import annotations

from concurrent import futures
from contextlib import contextmanager

import grpc
import pytest

from agent_for_mc_reranker.interfaces.grpc import reranker_pb2, reranker_pb2_grpc
from agent_for_mc_reranker.service import RerankerService


class FakeRanker:
    model_name_or_path = "fake-reranker"

    def __init__(self, scores: list[float] | None = None):
        self.scores = scores or []
        self.calls: list[tuple[str, list[str]]] = []

    def warmup(self) -> None:
        pass

    def compute_scores(self, query: str, passages: list[str]) -> list[float]:
        self.calls.append((query, list(passages)))
        return self.scores[: len(passages)]


@contextmanager
def running_server(ranker: FakeRanker, *, token: str = "secret-token"):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    reranker_pb2_grpc.add_RerankerServiceServicer_to_server(
        RerankerService(ranker=ranker, auth_token=token),
        server,
    )
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    channel = grpc.insecure_channel(f"127.0.0.1:{port}")
    try:
        yield reranker_pb2_grpc.RerankerServiceStub(channel)
    finally:
        channel.close()
        server.stop(None)


def test_health_reports_ready_and_model_name():
    with running_server(FakeRanker()) as stub:
        response = stub.Health(reranker_pb2.HealthRequest())

    assert response.ready is True
    assert response.model_name == "fake-reranker"


def test_rerank_requires_authorization():
    with running_server(FakeRanker([1.0])) as stub:
        with pytest.raises(grpc.RpcError) as exc_info:
            stub.Rerank(
                reranker_pb2.RerankRequest(
                    query="plugin",
                    documents=[
                        reranker_pb2.RerankDocument(
                            index=0,
                            document_id="doc-1",
                            text="content",
                        )
                    ],
                )
            )

    assert exc_info.value.code() == grpc.StatusCode.UNAUTHENTICATED


def test_empty_documents_return_empty_results():
    with running_server(FakeRanker()) as stub:
        response = stub.Rerank(
            reranker_pb2.RerankRequest(request_id="req-1", query="plugin"),
            metadata=(("authorization", "Bearer secret-token"),),
        )

    assert response.request_id == "req-1"
    assert list(response.results) == []


def test_rerank_sorts_by_score_and_preserves_tie_order():
    ranker = FakeRanker([0.5, 0.9, 0.9])
    with running_server(ranker) as stub:
        response = stub.Rerank(
            reranker_pb2.RerankRequest(
                request_id="req-1",
                query="plugin",
                documents=[
                    reranker_pb2.RerankDocument(index=0, document_id="a", text="A"),
                    reranker_pb2.RerankDocument(index=1, document_id="b", text="B"),
                    reranker_pb2.RerankDocument(index=2, document_id="c", text="C"),
                ],
            ),
            metadata=(("authorization", "Bearer secret-token"),),
        )

    assert [item.index for item in response.results] == [1, 2, 0]
    assert [item.document_id for item in response.results] == ["b", "c", "a"]
    assert ranker.calls == [("plugin", ["A", "B", "C"])]
