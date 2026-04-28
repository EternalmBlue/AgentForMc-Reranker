from __future__ import annotations

import os

from agent_for_mc_reranker.config import Settings


def test_settings_from_env_loads_config_and_token(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    config_path = tmp_path / "config.toml"
    env_file.write_text(
        'RAG_RERANKER_GRPC_AUTH_TOKEN="secret-token"\n',
        encoding="utf-8",
    )
    config_path.write_text(
        """
[reranker]
model_name_or_path = "local/model"

[grpc]
host = "0.0.0.0"
port = 50053
max_workers = 4

[runtime]
request_timeout_seconds = 30

[paths]
model_cache_dir = ".cache/test-models"
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("RAG_RERANKER_ENV_FILE", str(env_file))
    monkeypatch.setenv("RAG_RERANKER_CONFIG_TOML", str(config_path))
    monkeypatch.delenv("RAG_RERANKER_GRPC_AUTH_TOKEN", raising=False)

    settings = Settings.from_env()

    assert settings.auth_token == "secret-token"
    assert settings.model_name_or_path == "local/model"
    assert settings.host == "0.0.0.0"
    assert settings.port == 50053
    assert settings.max_workers == 4
    assert settings.request_timeout_seconds == 30
    assert settings.model_cache_dir == (tmp_path / ".cache/test-models").resolve()
    assert os.environ["HF_HOME"] == str(settings.model_cache_dir)
