"""Derive extra `codecarbon monitor` flags from the tracker constructor.

The option list is generated from ``BaseEmissionsTracker.__init__`` so it
stays aligned with the package API (issue #1273).
"""

from __future__ import annotations

import inspect
import re
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union, get_args, get_origin


_SKIP_PARAMS = {
    "self",
    "logging_logger",
    "output_handlers",
    "output_methods",
}

_DECLARED_ON_MONITOR = {
    "api_call_interval",
    "country_iso_code",
    "log_level",
    "measure_power_secs",
    "region",
    "save_to_api",
}


def _unwrap_optional(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is Union:
        non_none = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return annotation


def _eval_annotation(raw: str) -> Any:
    """Best-effort eval of a postponed annotation string."""
    namespace = {
        "Optional": Optional,
        "Union": Union,
        "List": list,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
    }
    try:
        return eval(raw, {"__builtins__": {}}, namespace)
    except Exception:
        return raw


def _cli_type(annotation: Any) -> Optional[type]:
    inner = _unwrap_optional(annotation)
    if inner in (str, int, float, bool):
        return inner
    return None


def _param_help_from_docstring(doc: Optional[str]) -> Dict[str, str]:
    if not doc:
        return {}
    help_map: Dict[str, str] = {}
    pattern = re.compile(
        r":param\s+(\w+)\s*:\s*(.+?)(?=\n\s*:param|\n\s*:return|\Z)",
        re.S,
    )
    for name, text in pattern.findall(doc):
        help_map[name] = " ".join(text.split())[:200]
    return help_map


def iter_tracker_cli_params() -> Iterable[Tuple[str, type, str]]:
    """Yield ``(name, python_type, help)`` for constructor args mapped to flags."""
    from codecarbon.emissions_tracker import BaseEmissionsTracker

    signature = inspect.signature(BaseEmissionsTracker.__init__)
    help_map = _param_help_from_docstring(BaseEmissionsTracker.__init__.__doc__)
    for name, param in signature.parameters.items():
        if name in _SKIP_PARAMS or name in _DECLARED_ON_MONITOR:
            continue
        annotation = param.annotation
        if isinstance(annotation, str):
            annotation = _eval_annotation(annotation)
        cli_type = _cli_type(annotation)
        if cli_type is None:
            continue
        yield name, cli_type, help_map.get(name, name.replace("_", " "))


def extra_tracker_param_names() -> List[str]:
    return [name for name, _, _ in iter_tracker_cli_params()]


def extend_monitor_signature(func: Callable) -> Callable:
    """Add generated keyword-only parameters so Typer exposes matching flags."""
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    existing = {param.name for param in params}
    extra = []
    for name, cli_type, _help_text in iter_tracker_cli_params():
        if name in existing:
            continue
        extra.append(
            inspect.Parameter(
                name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=Optional[cli_type],
            )
        )
    head = [p for p in params if p.kind != inspect.Parameter.VAR_KEYWORD]
    func.__signature__ = sig.replace(parameters=head + extra)
    return func
