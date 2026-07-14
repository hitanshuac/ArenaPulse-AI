"""Hub pipelines — refresh and ask.

This module is a backward-compatible re-export shim.  The actual
implementations now live in:

- :mod:`antigravity_engine.hub.refresh_pipeline`
- :mod:`antigravity_engine.hub.ask_pipeline`

All public symbols are re-exported so that existing ``from
antigravity_engine.hub.pipeline import ...`` statements continue
to work without changes.
"""
from __future__ import annotations

from antigravity_engine.hub.ask_pipeline import (  # noqa: F401
    _build_ask_context,
    _build_graph_skill_context,
    _build_retrieval_semantic_answer,
    _build_timeout_fallback_answer,
    _extract_blueprints_from_app,
    _extract_identifiers,
    _find_call_sites,
    _find_function_defs,
    _find_shell_call_sites,
    _find_shell_function_defs,
    _is_structure_query,
    _iter_python_files,
    _iter_shell_files,
    _read_context_file,
    ask_pipeline,
)

# Re-export everything from the split modules.
from antigravity_engine.hub.refresh_pipeline import (  # noqa: F401
    _build_fallback_conventions,
    _build_non_code_indexes,
    _build_scan_payload,
    _format_scan_report,
    _get_head_sha,
    refresh_pipeline,
)
