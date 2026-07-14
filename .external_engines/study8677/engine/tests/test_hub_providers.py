"""Tests for hub._providers multi-provider LLM failover."""
import asyncio
import json
from types import SimpleNamespace

import pytest
from antigravity_engine.hub import _providers
from antigravity_engine.hub._providers import (
    ProviderConfig,
    get_provider_chain,
    is_retryable_provider_error,
    run_with_provider_failover,
)


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        OPENAI_MODEL="primary-model",
        OPENAI_BASE_URL="https://primary/v1",
        OPENAI_API_KEY="primary-key",
    )


# --- classifier -----------------------------------------------------------


@pytest.mark.parametrize(
    "exc",
    [
        Exception("litellm.ServiceUnavailableError: Service temporarily unavailable"),
        Exception("HTTP 503 from upstream"),
        Exception("Connection refused"),
        TimeoutError("deadline exceeded"),
        TimeoutError(),
    ],
)
def test_is_retryable_provider_error_true(exc: Exception) -> None:
    assert is_retryable_provider_error(exc) is True


@pytest.mark.parametrize(
    "exc",
    [ValueError("bad question"), KeyError("missing"), RuntimeError("logic bug")],
)
def test_is_retryable_provider_error_false(exc: Exception) -> None:
    assert is_retryable_provider_error(exc) is False


# --- provider chain parsing ----------------------------------------------


def test_get_provider_chain_without_fallbacks_is_single(monkeypatch) -> None:
    monkeypatch.delenv("AG_LLM_FALLBACKS", raising=False)
    chain = get_provider_chain(_settings())
    assert len(chain) == 1
    assert chain[0].label == "primary"
    assert chain[0].model == "primary-model"
    assert chain[0].base_url == "https://primary/v1"


def test_get_provider_chain_parses_and_inherits(monkeypatch) -> None:
    monkeypatch.setenv(
        "AG_LLM_FALLBACKS",
        json.dumps(
            [
                {
                    "base_url": "https://backup/v1",
                    "api_key": "bk",
                    "model": "gpt-x",
                    "label": "backup",
                },
                {"model": "only-model"},  # inherits api_key, default label
            ]
        ),
    )
    chain = get_provider_chain(_settings())
    assert [p.label for p in chain] == ["primary", "backup", "fallback2"]
    assert chain[1] == ProviderConfig(
        model="gpt-x", base_url="https://backup/v1", api_key="bk", label="backup"
    )
    # Second fallback inherits the primary key and has no base_url.
    assert chain[2].api_key == "primary-key"
    assert chain[2].base_url == ""
    assert chain[2].model == "only-model"


def test_get_provider_chain_degrades_on_bad_json(monkeypatch) -> None:
    monkeypatch.setenv("AG_LLM_FALLBACKS", "not json {{")
    chain = get_provider_chain(_settings())
    assert len(chain) == 1


def test_get_provider_chain_degrades_on_non_array(monkeypatch) -> None:
    monkeypatch.setenv("AG_LLM_FALLBACKS", json.dumps({"model": "x"}))
    chain = get_provider_chain(_settings())
    assert len(chain) == 1


# --- failover wrapper -----------------------------------------------------


def test_failover_single_provider_is_passthrough(monkeypatch) -> None:
    """With one provider the operation runs once and env is left untouched."""
    activated: list[str] = []
    monkeypatch.setattr(
        _providers, "activate_provider", lambda p: activated.append(p.label)
    )

    async def op() -> str:
        return "ok"

    result = asyncio.run(
        run_with_provider_failover(
            op, providers=[ProviderConfig(model="m", label="primary")], label="ask"
        )
    )
    assert result == "ok"
    assert activated == []  # never touched the environment


def test_failover_switches_provider_on_transient_error(monkeypatch) -> None:
    activated: list[str] = []
    monkeypatch.setattr(
        _providers, "activate_provider", lambda p: activated.append(p.label)
    )
    calls = {"n": 0}

    async def op() -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            raise Exception("OpenAIException - Service temporarily unavailable")
        return "answered-on-backup"

    providers = [
        ProviderConfig(model="m1", label="primary"),
        ProviderConfig(model="m2", label="backup"),
    ]
    result = asyncio.run(
        run_with_provider_failover(op, providers=providers, label="ask")
    )
    assert result == "answered-on-backup"
    assert activated == ["primary", "backup"]
    assert calls["n"] == 2


def test_failover_does_not_retry_non_transient_error(monkeypatch) -> None:
    activated: list[str] = []
    monkeypatch.setattr(
        _providers, "activate_provider", lambda p: activated.append(p.label)
    )

    async def op() -> str:
        raise ValueError("genuine logic error")

    providers = [
        ProviderConfig(model="m1", label="primary"),
        ProviderConfig(model="m2", label="backup"),
    ]
    with pytest.raises(ValueError):
        asyncio.run(run_with_provider_failover(op, providers=providers, label="ask"))
    assert activated == ["primary"]  # no failover on a non-transient error
