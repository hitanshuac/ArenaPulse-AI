"""Multi-provider LLM failover for the Knowledge Hub.

The hub talks to a single OpenAI-compatible endpoint by default
(``OPENAI_BASE_URL`` / ``OPENAI_API_KEY`` / ``OPENAI_MODEL``).  When that
endpoint suffers a *sustained* outage, same-provider retries cannot help —
every retry hits the same dead host.  This module adds an opt-in ordered
list of backup providers (``AG_LLM_FALLBACKS``) plus a wrapper that re-runs
an operation against the next provider when the active one keeps failing
with a transient/provider error.

Behaviour is unchanged when ``AG_LLM_FALLBACKS`` is unset: the chain holds
exactly one provider and the wrapper is a pass-through with no environment
mutation.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from antigravity_engine.config import Settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Substrings (lower-cased) that mark an error as a transient provider failure.
# Kept as the single source of truth for both the retry path and failover.
_RETRYABLE_KEYWORDS = (
    "timeout",
    "gateway time-out",
    "504",
    "connection",
    "network",
    "unreachable",
    "refused",
    "rate limit",
    "ratelimit",
    "429",
    "502",
    "503",
    "500",
    "serviceunavailable",
    "service unavailable",
    "service temporarily unavailable",
    "temporarily unavailable",
    "bad gateway",
    "internalservererror",
    "internal server error",
)


def is_retryable_provider_error(exc: Exception) -> bool:
    """Return True for transient model/provider failures worth retrying.

    LiteLLM often wraps a provider 503 in an exception whose text preserves
    the wording ("Service temporarily unavailable") but not the numeric
    code, so the classifier matches on both.
    """
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return True
    msg = f"{type(exc).__module__}.{type(exc).__name__}: {exc}".lower()
    return any(keyword in msg for keyword in _RETRYABLE_KEYWORDS)


@dataclass(frozen=True)
class ProviderConfig:
    """One LLM endpoint: an OpenAI-compatible base URL, key, and model."""

    model: str
    base_url: str = ""
    api_key: str = ""
    label: str = "primary"


def get_provider_chain(settings: Settings) -> list[ProviderConfig]:
    """Build the ordered provider list: primary first, then fallbacks.

    The primary comes from the ``OPENAI_*`` settings.  Fallbacks are parsed
    from the ``AG_LLM_FALLBACKS`` env var — a JSON array of objects with
    optional ``base_url`` / ``api_key`` / ``model`` / ``label`` keys; a
    missing ``api_key`` or ``model`` inherits the primary's value.  A
    malformed value degrades to the primary alone and never breaks the
    default path.
    """
    primary = ProviderConfig(
        model=settings.OPENAI_MODEL,
        base_url=settings.OPENAI_BASE_URL,
        api_key=settings.OPENAI_API_KEY,
        label="primary",
    )
    chain = [primary]

    raw = os.environ.get("AG_LLM_FALLBACKS", "").strip()
    if not raw:
        return chain

    try:
        entries = json.loads(raw)
    except (ValueError, TypeError) as exc:
        logger.warning("Ignoring invalid AG_LLM_FALLBACKS (not JSON): %s", exc)
        return chain
    if not isinstance(entries, list):
        logger.warning("Ignoring AG_LLM_FALLBACKS: expected a JSON array")
        return chain

    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            logger.warning("Skipping non-object AG_LLM_FALLBACKS entry #%d", idx)
            continue
        model = str(entry.get("model") or primary.model).strip()
        if not model:
            logger.warning("Skipping AG_LLM_FALLBACKS entry #%d: empty model", idx)
            continue
        chain.append(
            ProviderConfig(
                model=model,
                base_url=str(entry.get("base_url") or "").strip(),
                api_key=str(entry.get("api_key") or primary.api_key),
                label=str(entry.get("label") or f"fallback{idx + 1}"),
            )
        )
    return chain


def activate_provider(provider: ProviderConfig) -> None:
    """Make ``provider`` the active LLM endpoint for subsequent agent calls.

    Sets the ``OPENAI_*`` environment variables and resets the cached
    settings so the next ``get_settings()`` / ``create_model()`` resolves to
    this provider.  ``litellm`` reads these at request time, so even
    already-built agents pick up the change on their next call.
    """
    from antigravity_engine.config import reset_settings

    os.environ["OPENAI_BASE_URL"] = provider.base_url or ""
    if provider.api_key:
        os.environ["OPENAI_API_KEY"] = provider.api_key
    os.environ["OPENAI_MODEL"] = provider.model
    reset_settings()


async def run_with_provider_failover(
    operation: Callable[[], Awaitable[T]],
    *,
    providers: list[ProviderConfig],
    is_retryable: Callable[[Exception], bool] | None = None,
    label: str = "operation",
) -> T:
    """Run ``operation`` against each provider until one succeeds.

    With a single provider the behaviour is unchanged: the operation runs
    once and the environment is left untouched.  With fallbacks configured, a
    transient/provider failure (per ``is_retryable``) on the active provider
    triggers a switch to the next provider and a full re-run.  A
    non-retryable error is raised immediately without failing over.
    """
    if is_retryable is None:
        is_retryable = is_retryable_provider_error

    # No fallback configured: preserve the exact default behaviour.
    if len(providers) <= 1:
        return await operation()

    last_exc: Exception | None = None
    for idx, provider in enumerate(providers):
        activate_provider(provider)
        try:
            return await operation()
        except Exception as exc:
            last_exc = exc
            is_last = idx >= len(providers) - 1
            if is_last or not is_retryable(exc):
                raise
            raw_msg = str(exc).replace("\n", " ").replace("\r", "")[:150]
            next_label = providers[idx + 1].label
            print(
                f"  ⚠ Provider '{provider.label}' failed for {label}: "
                f"{raw_msg or type(exc).__name__}. "
                f"Failing over to '{next_label}'...",
                file=sys.stderr,
            )

    # Unreachable: the loop returns on success or raises on the last provider.
    assert last_exc is not None
    raise last_exc
