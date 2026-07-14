from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read_text(path))


def require_contains(path: str, needle: str) -> None:
    if needle not in read_text(path):
        fail(f"{path} must contain {needle!r}")


def require_absent(path: str, pattern: str) -> None:
    text = read_text(path)
    if re.search(pattern, text):
        fail(f"{path} still matches legacy pattern {pattern!r}")


def check_plugin_versions() -> None:
    claude_plugin = read_json(".claude-plugin/plugin.json")
    claude_marketplace = read_json(".claude-plugin/marketplace.json")
    codex_plugin = read_json(".codex-plugin/plugin.json")
    engine_pyproject = read_text("engine/pyproject.toml")
    engine_init = read_text("engine/antigravity_engine/__init__.py")
    engine_version_match = re.search(
        r'^version = "([^"]+)"$', engine_pyproject, re.MULTILINE
    )
    init_version_match = re.search(
        r'^__version__ = "([^"]+)"$', engine_init, re.MULTILINE
    )
    if not engine_version_match or not init_version_match:
        fail("engine version must be declared in pyproject.toml and __init__.py")

    versions = {
        "engine_pyproject": engine_version_match.group(1),
        "engine_init": init_version_match.group(1),
        "claude_plugin": claude_plugin["version"],
        "claude_marketplace": claude_marketplace["plugins"][0]["version"],
        "codex_plugin": codex_plugin["version"],
    }
    if len(set(versions.values())) != 1:
        fail(f"plugin versions are not aligned: {versions}")


def check_python_contract() -> None:
    for path in ("engine/pyproject.toml", "cli/pyproject.toml"):
        require_contains(path, 'requires-python = ">=3.10"')

    for path in (
        "docs/en/QUICK_START.md",
        "docs/zh/QUICK_START.md",
        "docs/es/QUICK_START.md",
    ):
        require_absent(path, r"Python 3\.9\+")
        require_contains(path, "Python 3.10+")


def check_llm_configuration_docs() -> None:
    quick_start_paths = (
        "docs/en/QUICK_START.md",
        "docs/zh/QUICK_START.md",
        "docs/es/QUICK_START.md",
    )
    for path in quick_start_paths:
        require_contains(path, "OPENAI_BASE_URL=")
        require_contains(path, "OPENAI_API_KEY=")
        require_absent(path, r"GOOGLE_API_KEY=.*your")
        require_absent(path, r"GEMINI_MODEL_NAME")

    require_contains("engine/.env.example", "OPENAI_BASE_URL=")
    require_absent("engine/.env.example", r"GOOGLE_API_KEY")
    require_absent("engine/.env.example", r"GEMINI_MODEL_NAME")
    require_contains("docker-compose.yml", "OPENAI_BASE_URL=")
    require_absent("docker-compose.yml", r"\./\.context:/app/\.context")

    require_contains("commands/ag-setup.md", "OPENAI_BASE_URL=<chosen URL>")
    require_contains("commands/ag-setup.md", "OPENAI_MODEL=<chosen model>")
    require_absent("commands/ag-setup.md", r"Gemini|GOOGLE_API_KEY|GEMINI_MODEL_NAME")
    require_absent("engine/antigravity_engine/config.py", r"GOOGLE_API_KEY|GEMINI_MODEL_NAME")
    require_absent("engine/antigravity_engine/hub/agents.py", r"litellm/gemini|GOOGLE_API_KEY|GEMINI_MODEL_NAME")

    provider_setup_paths = (
        "engine/install.sh",
        "engine/install.bat",
        "engine/antigravity_engine/skills/agent_repo_init_core.py",
        "skills/agent-repo-init/scripts/init_project.py",
        "skills/agent-repo-init/SKILL.md",
        "engine/antigravity_engine/skills/agent-repo-init/SKILL.md",
    )
    for path in provider_setup_paths:
        require_contains(path, "ag-setup")
        require_absent(path, r"GEMINI_MODEL_NAME|GOOGLE_API_KEY")


def check_positioning_contract() -> None:
    require_contains(
        "README.md",
        "Cross-IDE repository knowledge engine for grounded codebase Q&A.",
    )
    require_contains("README.md", "## Support Matrix")
    require_contains(
        "docs/en/PHILOSOPHY.md",
        "Antigravity is that repository knowledge layer.",
    )
    require_contains("mission.md", "portable, evidence-grounded knowledge layer")
    require_contains("VERSIONING.md", "Plugin metadata must stay aligned")


def check_productization_contract() -> None:
    install_paths = ("engine/install.sh", "engine/install.bat")
    for path in install_paths:
        require_contains(path, "Python 3.10")
        require_contains(path, "ag-refresh --workspace .")
        require_contains(path, "ag-ask")
        require_absent(path, r"Python 3\.8")
        require_absent(path, r"python agent\.py")
        require_absent(path, r"GOOGLE_API_KEY=your_api_key_here")
        require_absent(path, r"MODEL_NAME=gemini-2\.0-flash-exp")

    active_sandbox_docs = (
        "README.md",
        "README_CN.md",
        "README_ES.md",
        "docs/en/QUICK_START.md",
        "docs/zh/QUICK_START.md",
        "docs/es/QUICK_START.md",
        "docs/en/SANDBOX.md",
        "docs/zh/SANDBOX.md",
        "docs/es/SANDBOX.md",
        "Dockerfile.sandbox",
    )
    for path in active_sandbox_docs:
        require_absent(path, r"SANDBOX_TYPE=docker")
        require_absent(path, r"Docker Sandbox")

    for path in (
        "docs/en/QUICK_START.md",
        "docs/zh/QUICK_START.md",
        "docs/es/QUICK_START.md",
    ):
        require_contains(path, "AG_RETRIEVAL_MODE")
        require_contains(path, "AG_ALLOW_MCP=true")
        require_contains(path, "ag-refresh --workspace .")
        require_contains(path, "ag-ask")
        require_absent(path, r"pytest --cov")

    for path in (
        "docs/en/MCP_INTEGRATION.md",
        "docs/zh/MCP_INTEGRATION.md",
        "docs/es/MCP_INTEGRATION.md",
        "INSTALL.md",
    ):
        require_contains(path, "AG_ALLOW_MCP=true")
        require_contains(path, "env")

    require_contains("engine/.env.example", "AG_RETRIEVAL_MODE=compact")
    require_contains("engine/.env.example", "AG_ALLOW_MCP=false")


def check_workflows() -> None:
    test_workflow = read_text(".github/workflows/test.yml")
    hygiene_workflow = read_text(".github/workflows/repo-hygiene.yml")
    combined = test_workflow + "\n" + hygiene_workflow
    require_contains(".github/workflows/test.yml", "actions/checkout@v5")
    require_contains(".github/workflows/test.yml", "actions/setup-python@v6")
    require_contains(
        ".github/workflows/test.yml",
        'python-version: ["3.10", "3.11", "3.12"]',
    )
    if "python scripts/check_repo_contract.py" not in hygiene_workflow:
        fail("repo hygiene workflow must run scripts/check_repo_contract.py")
    if "actions/checkout@v3" in combined or "actions/setup-python@v4" in combined:
        fail("workflows still use old checkout/setup-python actions")


def check_governance_assets() -> None:
    required_paths = (
        "CONTRIBUTING.md",
        "SECURITY.md",
        ".github/dependabot.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/ISSUE_TEMPLATE/config.yml",
    )
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        fail(f"missing governance assets: {', '.join(missing)}")


def main() -> None:
    check_plugin_versions()
    check_python_contract()
    check_llm_configuration_docs()
    check_positioning_contract()
    check_productization_contract()
    check_workflows()
    check_governance_assets()
    print("Repository contract check passed.")


if __name__ == "__main__":
    main()
