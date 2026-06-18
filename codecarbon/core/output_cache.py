"""
Process-level cache for output handler setup.

Reuses output handler instances and API clients across repeated tracker
lifecycles in the same process when configuration is unchanged.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional, Tuple

_cache_lock = threading.Lock()
_handlers: Dict[Tuple[Any, ...], object] = {}


def clear_cache() -> None:
    """Reset all cached output handlers and dependent client pools."""
    with _cache_lock:
        _handlers.clear()
    from codecarbon.core.api_client import clear_api_clients

    clear_api_clients()
    from codecarbon.output_methods.metrics.logfire import clear_logfire_cache

    clear_logfire_cache()


def get_file_output(output_file_name: str, output_dir: str, on_csv_write: str):
    from codecarbon.output_methods.file import FileOutput

    key = ("file", output_file_name, output_dir, on_csv_write)
    with _cache_lock:
        handler = _handlers.get(key)
        if handler is None:
            handler = FileOutput(output_file_name, output_dir, on_csv_write)
            _handlers[key] = handler
        return handler


def get_http_output(endpoint_url: str):
    from codecarbon.output_methods.http import HTTPOutput

    key = ("http", endpoint_url)
    with _cache_lock:
        handler = _handlers.get(key)
        if handler is None:
            handler = HTTPOutput(endpoint_url)
            _handlers[key] = handler
        return handler


def create_api_output(
    endpoint_url: str,
    experiment_id: Optional[str],
    api_key: Optional[str],
    conf,
):
    """Return a fresh API output wrapper backed by a pooled ApiClient."""
    from codecarbon.output_methods.http import CodeCarbonAPIOutput

    return CodeCarbonAPIOutput(
        endpoint_url=endpoint_url,
        experiment_id=experiment_id,
        api_key=api_key,
        conf=conf,
    )


def get_logfire_output():
    from codecarbon.output_methods.metrics.logfire import LogfireOutput

    key = ("logfire",)
    with _cache_lock:
        handler = _handlers.get(key)
        if handler is None:
            handler = LogfireOutput()
            _handlers[key] = handler
        return handler


def get_prometheus_output(prometheus_url: str, job_name: str):
    from codecarbon.output_methods.metrics.prometheus import PrometheusOutput

    key = ("prometheus", prometheus_url, job_name)
    with _cache_lock:
        handler = _handlers.get(key)
        if handler is None:
            handler = PrometheusOutput(prometheus_url, job_name)
            _handlers[key] = handler
        return handler


def get_boamps_output(output_dir: str):
    from codecarbon.output_methods.boamps import BoAmpsOutput

    key = ("boamps", output_dir)
    with _cache_lock:
        handler = _handlers.get(key)
        if handler is None:
            handler = BoAmpsOutput(output_dir=output_dir)
            _handlers[key] = handler
        return handler
