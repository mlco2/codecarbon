"""FastAPI/Starlette middleware for per-request emissions tracking."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from typing import Any

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
except ImportError as exc:
    raise ImportError(
        "CodeCarbon FastAPI integration requires Starlette (installed with FastAPI). "
        "Install optional dependencies with: pip install 'codecarbon[fastapi]'"
    ) from exc

from codecarbon import EmissionsTracker
from codecarbon.integrations.fastapi._headers import (
    HeaderConfig,
    HeaderFormatter,
    apply_response_headers,
    resolve_header_mapping,
)
from codecarbon.integrations.fastapi._routing import (
    DEFAULT_EXCLUDE_PATHS,
    build_task_name,
    should_skip_path,
)
from codecarbon.output_methods.emissions_data import EmissionsData


class CodeCarbonMiddleware(BaseHTTPMiddleware):
    """Measure emissions per HTTP request or attach to a shared app-level tracker."""

    def __init__(
        self,
        app: Any,
        *,
        project_name: str = "codecarbon-fastapi",
        tracking_mode: str = "request",
        exclude_paths: Iterable[str] | None = None,
        response_headers: HeaderConfig | None = None,
        include_emissions_header: bool = False,
        header_formatter: HeaderFormatter | None = None,
        task_name_formatter: Callable[[Request], str] | None = None,
        on_request_complete: Callable[..., Any] | None = None,
        tracker_kwargs: dict[str, Any] | None = None,
        **emissions_tracker_kwargs: Any,
    ) -> None:
        """Configure middleware.

        Args:
            app: ASGI application wrapped by this middleware.
            project_name: ``project_name`` passed to :class:`~codecarbon.EmissionsTracker`.
            tracking_mode: ``\"request\"`` (new tracker per request) or ``\"app\"`` (shared tracker).
            exclude_paths: Path prefixes to skip; defaults to common docs and health routes.
            response_headers: Preset name, field list, field-to-header mapping, or boolean.
            include_emissions_header: Deprecated; equivalent to ``response_headers=True``.
            header_formatter: If set, builds response headers instead of ``response_headers``.
            task_name_formatter: Overrides default route-based task naming.
            on_request_complete: Optional callback
                ``(request, response, emissions_data | None, task_name)``.
            tracker_kwargs: Baseline kwargs merged into the tracker constructor.
            **emissions_tracker_kwargs: Additional :class:`~codecarbon.EmissionsTracker` kwargs.
        """
        super().__init__(app)
        self.project_name = project_name
        self.tracking_mode = tracking_mode
        self.exclude_paths = set(exclude_paths or DEFAULT_EXCLUDE_PATHS)
        if response_headers is not None:
            self.header_mapping = resolve_header_mapping(response_headers)
        elif include_emissions_header:
            self.header_mapping = resolve_header_mapping(True)
        else:
            self.header_mapping = {}
        self.header_formatter = header_formatter
        self.task_name_formatter = task_name_formatter
        self.on_request_complete = on_request_complete
        merged: dict[str, Any] = dict(tracker_kwargs or {})
        merged.update(emissions_tracker_kwargs)
        merged.setdefault("allow_multiple_runs", True)
        self.tracker_kwargs = merged
        self._app_tracker: EmissionsTracker | None = None
        self._measurement_lock = asyncio.Lock()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Handle an incoming request behind CodeCarbon measurement."""
        if should_skip_path(request.url.path, self.exclude_paths):
            return await call_next(request)
        if self.tracking_mode == "app":
            return await self._dispatch_app_mode(request, call_next)
        return await self._dispatch_request_mode(request, call_next)

    def _apply_headers(
        self,
        response: Response | None,
        emissions_data: EmissionsData | None,
        request: Request,
    ) -> None:
        if response is None or emissions_data is None:
            return
        if self.header_formatter is not None:
            for name, value in self.header_formatter(emissions_data, request).items():
                response.headers[name] = value
            return
        apply_response_headers(response, emissions_data, self.header_mapping)

    async def _dispatch_request_mode(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        tracker = EmissionsTracker(project_name=self.project_name, **self.tracker_kwargs)
        tracker.start()
        response: Response | None = None
        emissions_data: EmissionsData | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            tracker.stop()
            emissions_data = getattr(tracker, "final_emissions_data", None)
            task_name = build_task_name(request, self.task_name_formatter)
            if self.on_request_complete is not None and response is not None:
                self.on_request_complete(request, response, emissions_data, task_name)
            self._apply_headers(response, emissions_data, request)

    async def _dispatch_app_mode(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        tracker = self._get_app_tracker(request)
        task_name = build_task_name(request, self.task_name_formatter)
        response: Response | None = None
        emissions_data: EmissionsData | None = None
        async with self._measurement_lock:
            await asyncio.to_thread(tracker.start_task, task_name)
            try:
                response = await call_next(request)
            finally:
                emissions_data = await asyncio.to_thread(tracker.stop_task, task_name)
        if self.on_request_complete is not None and response is not None:
            self.on_request_complete(request, response, emissions_data, task_name)
        self._apply_headers(response, emissions_data, request)
        return response

    def _get_app_tracker(self, request: Request) -> EmissionsTracker:
        app_tracker = getattr(request.app.state, "codecarbon_tracker", None)
        if app_tracker is not None:
            return app_tracker
        if self._app_tracker is None:
            self._app_tracker = EmissionsTracker(project_name=self.project_name, **self.tracker_kwargs)
            self._app_tracker.start()
        return self._app_tracker


def add_codecarbon_middleware(app: Any, **kwargs: Any) -> None:
    """Register :class:`CodeCarbonMiddleware` on a FastAPI or Starlette app.

    Args:
        app: Application instance with ``add_middleware``.
        **kwargs: Forwarded to :class:`CodeCarbonMiddleware`.
    """
    app.add_middleware(CodeCarbonMiddleware, **kwargs)
