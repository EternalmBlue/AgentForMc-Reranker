from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_for_mc_reranker.runtime_paths import (
    default_config_path,
    default_dotenv_path,
    ensure_external_runtime_layout,
    resolve_runtime_path,
    runtime_base_dir,
)

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]


BASE_DIR = runtime_base_dir()
DEFAULT_CONFIG_PATH = default_config_path()
DEFAULT_MODEL_NAME = "maidalun1020/bce-reranker-base_v1"


def _load_dotenv() -> None:
    configured_path = os.getenv("RAG_RERANKER_ENV_FILE")
    env_path = (
        resolve_runtime_path(configured_path, base_dir=BASE_DIR)
        if configured_path
        else default_dotenv_path()
    )
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _load_toml_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return data if isinstance(data, dict) else {}


def _config_value(
    config: dict[str, Any],
    section: str,
    key: str,
    default: Any,
) -> Any:
    section_data = config.get(section, {})
    if not isinstance(section_data, dict):
        return default
    return section_data.get(key, default)


def _resolve_path(path_value: str | Path, *, base_dir: Path) -> Path:
    return resolve_runtime_path(path_value, base_dir=base_dir)


def _configure_model_cache_env(model_cache_dir: Path) -> None:
    model_cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(model_cache_dir)
    os.environ["HF_HUB_CACHE"] = str(model_cache_dir / "huggingface_hub")
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(model_cache_dir / "huggingface_hub")
    os.environ["TRANSFORMERS_CACHE"] = str(model_cache_dir / "transformers")
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(
        model_cache_dir / "sentence_transformers"
    )


@dataclass(frozen=True, slots=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 50052
    max_workers: int = 2
    request_timeout_seconds: int = 60
    model_name_or_path: str = DEFAULT_MODEL_NAME
    model_cache_dir: Path = BASE_DIR / ".cache" / "models"
    auth_token: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        configured_path = os.getenv("RAG_RERANKER_CONFIG_TOML")
        config_path = _resolve_path(
            configured_path or DEFAULT_CONFIG_PATH,
            base_dir=BASE_DIR,
        )
        ensure_external_runtime_layout(
            config_path=config_path,
            copy_default_config=configured_path is None,
        )
        config = _load_toml_config(config_path)
        config_base_dir = config_path.parent
        model_cache_dir = _resolve_path(
            str(_config_value(config, "paths", "model_cache_dir", ".cache/models"))
            or ".cache/models",
            base_dir=config_base_dir,
        )
        _configure_model_cache_env(model_cache_dir)
        return cls(
            host=str(_config_value(config, "grpc", "host", "127.0.0.1"))
            or "127.0.0.1",
            port=int(str(_config_value(config, "grpc", "port", 50052)) or "50052"),
            max_workers=int(
                str(_config_value(config, "grpc", "max_workers", 2)) or "2"
            ),
            request_timeout_seconds=int(
                str(_config_value(config, "runtime", "request_timeout_seconds", 60))
                or "60"
            ),
            model_name_or_path=str(
                _config_value(
                    config,
                    "reranker",
                    "model_name_or_path",
                    DEFAULT_MODEL_NAME,
                )
            )
            or DEFAULT_MODEL_NAME,
            model_cache_dir=model_cache_dir,
            auth_token=os.getenv("RAG_RERANKER_GRPC_AUTH_TOKEN"),
        )


def validate_settings(settings: Settings) -> None:
    if not settings.auth_token or not settings.auth_token.strip():
        raise ValueError(
            "Missing reranker auth token. Set RAG_RERANKER_GRPC_AUTH_TOKEN."
        )
    if settings.port < 1 or settings.port > 65535:
        raise ValueError("grpc.port must be within 1..65535.")
    if settings.max_workers < 1:
        raise ValueError("grpc.max_workers must be > 0.")
    if settings.request_timeout_seconds < 1:
        raise ValueError("runtime.request_timeout_seconds must be > 0.")
