"""Tests for hub.agents.create_model() LLM backend resolution."""
import pytest
from antigravity_engine.hub.agents import create_model


def _make_settings(**overrides):
    """Build a minimal Settings-like object for create_model."""
    defaults = {
        "OPENAI_API_KEY": "",
        "OPENAI_BASE_URL": "",
        "OPENAI_MODEL": "gpt-4o-mini",
    }
    defaults.update(overrides)

    class _FakeSettings:
        pass

    s = _FakeSettings()
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


def test_openai_key_only_returns_model_name():
    """Standard OpenAI (key but no custom base URL) returns raw model name."""
    settings = _make_settings(OPENAI_API_KEY="sk-test")
    result = create_model(settings)
    assert result == "gpt-4o-mini"


def test_base_url_routes_through_litellm():
    """Custom base URL (Ollama, NVIDIA, etc.) routes through litellm."""
    settings = _make_settings(OPENAI_BASE_URL="http://localhost:11434/v1")
    result = create_model(settings)
    assert result.startswith("litellm/openai/")
    assert "gpt-4o-mini" in result


def test_base_url_with_key_routes_through_litellm():
    """Custom base URL + API key (NVIDIA) routes through litellm, not raw."""
    settings = _make_settings(
        OPENAI_BASE_URL="https://integrate.api.nvidia.com/v1",
        OPENAI_API_KEY="nvapi-test-key",
        OPENAI_MODEL="moonshotai/kimi-k2.5",
    )
    result = create_model(settings)
    assert result == "litellm/openai/moonshotai/kimi-k2.5"


def test_ag_setup_openai_config_ignores_unrelated_provider_attrs():
    settings = _make_settings(
        GOOGLE_API_KEY="goog-key-123",
        OPENAI_BASE_URL="https://api.deepseek.com/v1",
        OPENAI_API_KEY="deepseek-key",
        OPENAI_MODEL="deepseek-chat",
    )
    result = create_model(settings)
    assert result == "litellm/openai/deepseek-chat"


def test_no_config_raises_value_error():
    settings = _make_settings()
    with pytest.raises(ValueError, match="No LLM configured"):
        create_model(settings)
