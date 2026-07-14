"""Tests for the Claude plugin engine install hook."""

from __future__ import annotations

import subprocess
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_hook_module() -> ModuleType:
    hook_path = REPO_ROOT / "hooks" / "install_engine.py"
    spec = spec_from_file_location("install_engine_hook", hook_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load hook module")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_read_project_version(tmp_path: Path) -> None:
    hook = _load_hook_module()
    engine_dir = tmp_path / "engine"
    engine_dir.mkdir()
    (engine_dir / "pyproject.toml").write_text(
        '[project]\nname = "antigravity-engine"\nversion = "0.2.1"\n',
        encoding="utf-8",
    )

    assert hook.read_project_version(engine_dir) == "0.2.1"


def test_get_installed_engine_version_parses_ag_mcp_version(monkeypatch) -> None:
    hook = _load_hook_module()

    monkeypatch.setattr(hook.shutil, "which", lambda cmd: "/tmp/ag-mcp")

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="ag-mcp 0.2.1\n",
            stderr="",
        )

    monkeypatch.setattr(hook.subprocess, "run", fake_run)

    assert hook.get_installed_engine_version() == "0.2.1"


def test_needs_engine_install_or_upgrade() -> None:
    hook = _load_hook_module()

    assert hook.needs_engine_install_or_upgrade("0.2.0", "0.2.1") is True
    assert hook.needs_engine_install_or_upgrade(None, "0.2.1") is True
    assert hook.needs_engine_install_or_upgrade("0.2.1", None) is True
    assert hook.needs_engine_install_or_upgrade("0.2.1", "0.2.1") is False


def test_existing_old_ag_mcp_triggers_pipx_upgrade(tmp_path: Path, monkeypatch) -> None:
    hook = _load_hook_module()
    plugin_root = tmp_path / "plugin"
    engine_dir = plugin_root / "engine"
    (plugin_root / "cli").mkdir(parents=True)
    engine_dir.mkdir(parents=True)
    (engine_dir / "pyproject.toml").write_text(
        '[project]\nname = "antigravity-engine"\nversion = "0.2.1"\n',
        encoding="utf-8",
    )
    calls: list[list[str]] = []

    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setattr(hook, "prepend_path", lambda path: None)
    monkeypatch.setattr(hook, "user_scripts_bin", lambda: None)
    monkeypatch.setattr(hook, "has", lambda cmd: cmd in {"ag-mcp", "pipx"})
    monkeypatch.setattr(hook, "get_installed_engine_version", lambda: "0.2.0")
    monkeypatch.setattr(hook, "pipx", lambda args: calls.append(args) or 0)
    monkeypatch.setattr(hook, "run", lambda args: 0)

    assert hook.main() == 0
    assert ["install", "--force", str(engine_dir)] in calls


def test_missing_ag_mcp_uses_first_install_path(tmp_path: Path, monkeypatch) -> None:
    hook = _load_hook_module()
    plugin_root = tmp_path / "plugin"
    engine_dir = plugin_root / "engine"
    (plugin_root / "cli").mkdir(parents=True)
    engine_dir.mkdir(parents=True)
    (engine_dir / "pyproject.toml").write_text(
        '[project]\nname = "antigravity-engine"\nversion = "0.2.1"\n',
        encoding="utf-8",
    )
    calls: list[list[str]] = []
    installed = False

    def fake_has(cmd: str) -> bool:
        if cmd == "ag-mcp":
            return installed
        if cmd == "pipx":
            return True
        return False

    def fake_pipx(args: list[str]) -> int:
        nonlocal installed
        calls.append(args)
        if args[:1] == ["install"]:
            installed = True
        return 0

    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setattr(hook, "prepend_path", lambda path: None)
    monkeypatch.setattr(hook, "user_scripts_bin", lambda: None)
    monkeypatch.setattr(hook, "has", fake_has)
    monkeypatch.setattr(hook, "get_installed_engine_version", lambda: None)
    monkeypatch.setattr(hook, "ensure_pipx", lambda: True)
    monkeypatch.setattr(hook, "pipx", fake_pipx)
    monkeypatch.setattr(hook, "run", lambda args: 0)

    assert hook.main() == 0
    assert calls == [["ensurepath"], ["install", "--force", str(engine_dir)]]


def test_existing_matching_ag_mcp_skips_install(tmp_path: Path, monkeypatch) -> None:
    hook = _load_hook_module()
    plugin_root = tmp_path / "plugin"
    engine_dir = plugin_root / "engine"
    engine_dir.mkdir(parents=True)
    (engine_dir / "pyproject.toml").write_text(
        '[project]\nname = "antigravity-engine"\nversion = "0.2.1"\n',
        encoding="utf-8",
    )
    calls: list[list[str]] = []

    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setattr(hook, "prepend_path", lambda path: None)
    monkeypatch.setattr(hook, "user_scripts_bin", lambda: None)
    monkeypatch.setattr(hook, "has", lambda cmd: cmd == "ag-mcp")
    monkeypatch.setattr(hook, "get_installed_engine_version", lambda: "0.2.1")
    monkeypatch.setattr(hook, "pipx", lambda args: calls.append(args) or 0)

    assert hook.main() == 0
    assert calls == []


def test_pipx_unavailable_falls_back_to_pip_user_upgrade(tmp_path: Path, monkeypatch) -> None:
    hook = _load_hook_module()
    plugin_root = tmp_path / "plugin"
    engine_dir = plugin_root / "engine"
    cli_dir = plugin_root / "cli"
    cli_dir.mkdir(parents=True)
    engine_dir.mkdir(parents=True)
    (engine_dir / "pyproject.toml").write_text(
        '[project]\nname = "antigravity-engine"\nversion = "0.2.1"\n',
        encoding="utf-8",
    )
    run_calls: list[list[str]] = []

    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setattr(hook, "prepend_path", lambda path: None)
    monkeypatch.setattr(hook, "user_scripts_bin", lambda: None)
    monkeypatch.setattr(hook, "has", lambda cmd: cmd == "ag-mcp")
    monkeypatch.setattr(hook, "get_installed_engine_version", lambda: "0.2.0")
    monkeypatch.setattr(hook, "ensure_pipx", lambda: False)
    monkeypatch.setattr(hook, "pipx", lambda args: (_ for _ in ()).throw(AssertionError("pipx should not run")))

    def fake_run(args: list[str]) -> int:
        run_calls.append(args)
        return 0

    monkeypatch.setattr(hook, "run", fake_run)

    assert hook.main() == 0
    py = hook.sys.executable or ("python" if hook.has("python") else "python3")
    assert run_calls == [
        [
            py,
            "-m",
            "pip",
            "install",
            "--user",
            "--upgrade",
            "--quiet",
            str(engine_dir),
            str(cli_dir),
        ]
    ]


def test_pipx_unavailable_pip_failure_returns_nonzero_and_prints_manual_upgrade(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    hook = _load_hook_module()
    plugin_root = tmp_path / "plugin"
    engine_dir = plugin_root / "engine"
    cli_dir = plugin_root / "cli"
    cli_dir.mkdir(parents=True)
    engine_dir.mkdir(parents=True)
    (engine_dir / "pyproject.toml").write_text(
        '[project]\nname = "antigravity-engine"\nversion = "0.2.1"\n',
        encoding="utf-8",
    )
    run_calls: list[list[str]] = []

    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setattr(hook, "prepend_path", lambda path: None)
    monkeypatch.setattr(hook, "user_scripts_bin", lambda: None)
    monkeypatch.setattr(hook, "has", lambda cmd: cmd == "ag-mcp")
    monkeypatch.setattr(hook, "get_installed_engine_version", lambda: "0.2.0")
    monkeypatch.setattr(hook, "ensure_pipx", lambda: False)
    monkeypatch.setattr(hook, "pipx", lambda args: (_ for _ in ()).throw(AssertionError("pipx should not run")))

    def fake_run(args: list[str]) -> int:
        run_calls.append(args)
        return 1

    monkeypatch.setattr(hook, "run", fake_run)

    assert hook.main() == 1
    err = capsys.readouterr().err
    assert "AUTO-INSTALL FAILED" in err
    assert f'python -m pip install --user --upgrade "{engine_dir}" "{cli_dir}"' in err
    assert run_calls
