from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from concurrent import futures

import grpc

from agent_for_mc_reranker.config import Settings, validate_settings
from agent_for_mc_reranker.interfaces.grpc import reranker_pb2_grpc
from agent_for_mc_reranker.model import BceReranker
from agent_for_mc_reranker.service import RerankerService


LOGGER = logging.getLogger(__name__)


def serve(settings: Settings | None = None) -> None:
    resolved_settings = settings or Settings.from_env()
    validate_settings(resolved_settings)

    ranker = BceReranker(resolved_settings.model_name_or_path)
    ranker.warmup()

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=resolved_settings.max_workers)
    )
    reranker_pb2_grpc.add_RerankerServiceServicer_to_server(
        RerankerService(
            ranker=ranker,
            auth_token=resolved_settings.auth_token or "",
        ),
        server,
    )

    listen_address = f"{resolved_settings.host}:{resolved_settings.port}"
    bound_port = server.add_insecure_port(listen_address)
    if bound_port == 0:
        raise RuntimeError(f"reranker gRPC service failed to bind: {listen_address}")

    LOGGER.info("AgentForMc reranker gRPC service listening on %s", listen_address)
    server.start()
    try:
        server.wait_for_termination()
    finally:
        server.stop(grace=None)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AgentForMc reranker gRPC middleware")
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="load config and validate required runtime settings without starting gRPC",
    )
    args = parser.parse_args(argv)

    try:
        settings = Settings.from_env()
        validate_settings(settings)
        if args.self_check:
            print(
                "reranker self-check ok: "
                f"{settings.host}:{settings.port} model={settings.model_name_or_path}"
            )
            return 0
        serve(settings)
    except KeyboardInterrupt:
        print("\nreranker service stopped.")
        return 0
    except Exception as exc:
        print(f"[reranker startup error] {exc}")
        return 1
    return 0
