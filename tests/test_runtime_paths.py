from __future__ import annotations

from agent_for_mc_reranker import runtime_paths


def test_runtime_base_dir_uses_executable_parent_when_frozen(tmp_path, monkeypatch):
    executable = tmp_path / "AgentForMc-Reranker.exe"

    monkeypatch.setattr(runtime_paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(runtime_paths.sys, "executable", str(executable))

    assert runtime_paths.runtime_base_dir() == tmp_path.resolve()
    assert runtime_paths.default_config_path() == (tmp_path / "config.toml").resolve()
    assert runtime_paths.default_dotenv_path() == (tmp_path / ".env").resolve()


def test_ensure_external_runtime_layout_copies_bundled_config_when_frozen(
    tmp_path,
    monkeypatch,
):
    bundle_dir = tmp_path / "bundle"
    runtime_dir = tmp_path / "runtime"
    bundle_dir.mkdir()
    (bundle_dir / "config.toml").write_text("[grpc]\nport = 50052\n", encoding="utf-8")

    monkeypatch.setattr(runtime_paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        runtime_paths.sys,
        "executable",
        str(runtime_dir / "AgentForMc-Reranker.exe"),
    )
    monkeypatch.setattr(runtime_paths.sys, "_MEIPASS", str(bundle_dir), raising=False)

    config_path = runtime_paths.ensure_external_runtime_layout()

    assert config_path == (runtime_dir / "config.toml").resolve()
    assert config_path.read_text(encoding="utf-8") == "[grpc]\nport = 50052\n"
    assert (runtime_dir / ".cache" / "models").is_dir()
