import functools
from collections.abc import Callable
from typing import Any

from arenapulse.engine import ArenaEngine


def guard(engine: ArenaEngine, action_type: str, payload_extractor: Callable[..., Any] | None = None):
    """
    Decorator that intercepts function calls, validating their arguments through an ArenaEngine instance.

    Usage:
        @guard(engine, action_type="write_file", payload_extractor=lambda filepath, **kw: filepath)
        def save_report(filepath: str, content: str):
            ...
    """
    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if payload_extractor:
                payload = payload_extractor(*args, **kwargs)
            else:
                payload = kwargs if kwargs else (args[0] if args else {})

            engine.verify_and_execute(action_type, payload)
            return func(*args, **kwargs)

        return wrapper

    return decorator
