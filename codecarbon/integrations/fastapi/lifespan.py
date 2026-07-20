"""Lifespan helpers for sharing one ``EmissionsTracker`` across requests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from typing import Any

from codecarbon import EmissionsTracker
from codecarbon.integrations.fastapi.middleware import shutdown_codecarbon_middleware


@asynccontextmanager
async def create_codecarbon_lifespan(
    app: Any,
    *,
    project_name: str = "codecarbon-fastapi",
    **tracker_kwargs: Any,
) -> AsyncIterator[None]:
    """Start a tracker for the app lifetime and expose it on ``app.state``.

    Args:
        app: Starlette/FastAPI application with ``state`` namespace.
        project_name: ``project_name`` for :class:`~codecarbon.EmissionsTracker`.
        **tracker_kwargs: Extra constructor kwargs for the tracker.

    Yields:
        ``None`` while the app runs.
    """
    merged = dict(tracker_kwargs)
    merged.setdefault("allow_multiple_runs", True)
    tracker = EmissionsTracker(project_name=project_name, **merged)
    tracker.start()
    app.state.codecarbon_tracker = tracker
    try:
        yield
    finally:
        tracker.stop()
        app.state.codecarbon_tracker = None
        shutdown_codecarbon_middleware(app)


def compose_lifespans(
    *factories: Callable[[Any], AbstractAsyncContextManager[Any]],
) -> Callable[[Any], AbstractAsyncContextManager[None]]:
    """Nest multiple lifespan context managers into one FastAPI lifespan.

    FastAPI accepts a single ``lifespan`` handler. Use this helper to stack
    CodeCarbon with database, cache, or other startup/shutdown contexts::

        app = FastAPI(
            lifespan=compose_lifespans(
                lambda a: create_codecarbon_lifespan(a, project_name="my-api"),
                lambda a: db_lifespan(a),
            )
        )

    Args:
        *factories: Callables that take the app and return an async context manager.

    Returns:
        A lifespan callable suitable for ``FastAPI(lifespan=...)``.
    """

    @asynccontextmanager
    async def lifespan(app: Any) -> AsyncIterator[None]:
        async with AsyncExitStack() as stack:
            for factory in factories:
                await stack.enter_async_context(factory(app))
            yield

    return lifespan
