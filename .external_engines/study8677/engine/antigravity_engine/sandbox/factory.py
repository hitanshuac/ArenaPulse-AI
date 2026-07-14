import os
import sys

from .base import CodeSandbox
from .local import LocalSandbox


def get_sandbox() -> CodeSandbox:
    """Factory method to obtain the configured executor.

    Supported types: local (default), microsandbox (opt-in), e2b (future).
    Falls back to local for developer convenience, with an explicit warning so
    callers do not mistake the fallback for an isolated sandbox.
    """
    mode = os.getenv("SANDBOX_TYPE", "local").lower()

    if mode == "microsandbox":
        try:
            from .microsandbox_exec import MicrosandboxSandbox  # type: ignore

            return MicrosandboxSandbox()
        except Exception as exc:
            print(
                "Warning: SANDBOX_TYPE=microsandbox requested but unavailable; "
                f"falling back to local trusted-workspace execution ({exc}).",
                file=sys.stderr,
            )
            return LocalSandbox()

    if mode == "e2b":
        try:
            from .e2b_exec import E2BSandbox  # type: ignore

            return E2BSandbox()
        except Exception as exc:
            print(
                "Warning: SANDBOX_TYPE=e2b requested but unavailable; "
                f"falling back to local trusted-workspace execution ({exc}).",
                file=sys.stderr,
            )
            return LocalSandbox()

    if mode != "local":
        print(
            f"Warning: SANDBOX_TYPE={mode} is not a supported runtime; "
            "falling back to local trusted-workspace execution.",
            file=sys.stderr,
        )
    return LocalSandbox()
