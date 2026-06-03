"""Lifespan helpers for sharing one ``EmissionsTracker`` across requests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from codecarbon import EmissionsTracker


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
