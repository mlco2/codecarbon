"""Route naming and endpoint filter helpers for FastAPI/Starlette."""

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.requests import Request

DEFAULT_EXCLUDE: frozenset[str] = frozenset(
    {
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/healthz",
        "/ready",
        "/live",
    }
)

HTTP_METHODS = frozenset(
    {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE", "CONNECT"}
)


def get_endpoint_path(request: "Request") -> str:
    """Return the mounted route template or the raw URL path.

    Args:
        request: Current Starlette/FastAPI request.

    Returns:
        Route template such as ``/items/{item_id}``, or ``request.url.path``.
    """
    route = request.scope.get("route")
    if route is not None:
        return route.path
    return request.url.path


def build_endpoint_key(request: "Request") -> str:
    """Build a stable endpoint identifier such as ``GET /predict``.

    Args:
        request: Current Starlette/FastAPI request.

    Returns:
        HTTP method plus route template or URL path.
    """
    return f"{request.method} {get_endpoint_path(request)}"


def is_method_pattern(pattern: str) -> bool:
    """Return True when ``pattern`` is ``METHOD /path``."""
    method, _, path = pattern.partition(" ")
    return method in HTTP_METHODS and path.startswith("/")


def matches_exclude(
    pattern: str,
    url_path: str,
    endpoint_key: str,
    endpoint_path: str,
) -> bool:
    """Return True when an exclude pattern matches the request."""
    if is_method_pattern(pattern):
        return endpoint_key == pattern
    if not pattern.startswith("/"):
        return endpoint_key == pattern
    return (
        url_path == pattern
        or url_path.startswith(f"{pattern}/")
        or endpoint_path == pattern
    )


def matches_include(pattern: str, endpoint_key: str, endpoint_path: str) -> bool:
    """Return True when an include pattern matches the request."""
    if is_method_pattern(pattern):
        return endpoint_key == pattern
    if pattern.startswith("/"):
        return endpoint_path == pattern
    return endpoint_key == pattern


def should_track_request(
    request: "Request",
    include: Iterable[str] | None,
    exclude: Iterable[str],
) -> bool:
    """Return True when the request should be measured.

    Patterns use one of two forms:

    * ``METHOD /route/template`` — one HTTP method on one route (e.g. ``GET /predict``)
    * ``/route/template`` — any method on that route, or a URL path prefix when excluding

    Args:
        request: Current Starlette/FastAPI request.
        include: When set, only matching endpoints are tracked.
        exclude: Endpoints or URL prefixes to skip.

    Returns:
        True when CodeCarbon should track this request.
    """
    url_path = request.url.path
    endpoint_key = build_endpoint_key(request)
    endpoint_path = get_endpoint_path(request)
    for pattern in exclude:
        if matches_exclude(pattern, url_path, endpoint_key, endpoint_path):
            return False
    if include is None:
        return True
    return any(matches_include(pattern, endpoint_key, endpoint_path) for pattern in include)


def build_task_name(
    request: "Request",
    formatter: Callable[["Request"], str] | None = None,
) -> str:
    """Derive a stable label like ``GET /items/{item_id}`` for task-scoped tracking.

    Args:
        request: Current Starlette/FastAPI request.
        formatter: Optional function that returns the task name instead of the default.

    Returns:
        Method plus route template when a route is mounted on the request scope,
        otherwise method plus the raw URL path.
    """
    if formatter is not None:
        return formatter(request)
    return build_endpoint_key(request)
