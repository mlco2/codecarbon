"""Route naming and endpoint filter helpers for FastAPI/Starlette."""

from collections.abc import Iterable
from typing import TYPE_CHECKING

from codecarbon.core.emission_fields import HttpMethod

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

HTTP_METHODS = frozenset(method.value for method in HttpMethod)


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
    return method in HttpMethod.__members__ and path.startswith("/")


def matches_filter_pattern(
    pattern: str,
    endpoint_key: str,
    endpoint_path: str,
    url_path: str,
    *,
    exclude: bool,
) -> bool:
    """Return True when an include or exclude pattern matches the request."""
    if is_method_pattern(pattern):
        return endpoint_key == pattern
    if not pattern.startswith("/"):
        return endpoint_key == pattern
    if exclude:
        return (
            url_path == pattern
            or url_path.startswith(f"{pattern}/")
            or endpoint_path == pattern
        )
    return endpoint_path == pattern


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
    if include is None:
        needs_full_match = any(is_method_pattern(pattern) for pattern in exclude)
        if not needs_full_match:
            for pattern in exclude:
                if url_path == pattern or url_path.startswith(f"{pattern}/"):
                    return False
            return True
    endpoint_key = build_endpoint_key(request)
    endpoint_path = get_endpoint_path(request)
    for pattern in exclude:
        if matches_filter_pattern(
            pattern,
            endpoint_key,
            endpoint_path,
            url_path,
            exclude=True,
        ):
            return False
    if include is None:
        return True
    return any(
        matches_filter_pattern(
            pattern,
            endpoint_key,
            endpoint_path,
            url_path,
            exclude=False,
        )
        for pattern in include
    )
