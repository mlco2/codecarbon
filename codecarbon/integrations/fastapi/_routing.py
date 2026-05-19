"""Route naming and path exclusion helpers for FastAPI/Starlette."""

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.requests import Request

DEFAULT_EXCLUDE_PATHS: frozenset[str] = frozenset(
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


def should_skip_path(path: str, exclude_paths: Iterable[str]) -> bool:
    """Return True if ``path`` matches an excluded prefix (exact or with a trailing segment).

    Args:
        path: Request path such as ``/docs`` or ``/api/v1/runs``.
        exclude_paths: Iterable of path prefixes (e.g. ``/health``, ``/docs``).

    Returns:
        True when this path should bypass CodeCarbon tracking.
    """
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in exclude_paths)


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
    route = request.scope.get("route")
    if route is not None:
        return f"{request.method} {route.path}"
    return f"{request.method} {request.url.path}"
