from antigravity_engine.sandbox.factory import get_sandbox
from antigravity_engine.sandbox.local import LocalSandbox
from antigravity_engine.sandbox.microsandbox_exec import MicrosandboxSandbox


def test_factory_default_local(monkeypatch):
    monkeypatch.delenv("SANDBOX_TYPE", raising=False)
    s = get_sandbox()
    assert isinstance(s, LocalSandbox)


def test_factory_microsandbox_resolution(monkeypatch):
    # When microsandbox is requested, factory should return MicrosandboxSandbox instance
    monkeypatch.setenv("SANDBOX_TYPE", "microsandbox")
    s = get_sandbox()
    assert isinstance(s, MicrosandboxSandbox)


def test_factory_legacy_docker_value_falls_back_to_local(monkeypatch, capsys):
    monkeypatch.setenv("SANDBOX_TYPE", "docker")
    s = get_sandbox()
    captured = capsys.readouterr()
    assert isinstance(s, LocalSandbox)
    assert "SANDBOX_TYPE=docker is not a supported runtime" in captured.err


def test_factory_unavailable_runtime_warns_before_local_fallback(monkeypatch, capsys):
    monkeypatch.setenv("SANDBOX_TYPE", "e2b")

    s = get_sandbox()
    captured = capsys.readouterr()

    assert isinstance(s, LocalSandbox)
    assert "SANDBOX_TYPE=e2b requested but unavailable" in captured.err
    assert "falling back to local trusted-workspace execution" in captured.err
