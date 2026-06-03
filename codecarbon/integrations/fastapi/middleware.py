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
    DEFAULT_EXCLUDE,
    build_task_name,
    should_track_request,
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
        include: Iterable[str] | None = None,
        exclude: Iterable[str] | None = None,
        response_headers: HeaderConfig | None = None,
        include_emissions_header: bool = False,
        header_formatter: HeaderFormatter | None = None,
        task_name_formatter: Callable[[Request], str] | None = None,
        on_request_complete: Callable[..., Any] | None = None,
        tracker_kwargs: dict[str, Any] | None = None,
        defer_measurement: bool = False,
        **emissions_tracker_kwargs: Any,
    ) -> None:
        """Configure middleware.

        Args:
            app: ASGI application wrapped by this middleware.
            project_name: ``project_name`` passed to :class:`~codecarbon.EmissionsTracker`.
            tracking_mode: ``\"request\"`` (new tracker per request) or ``\"app\"`` (shared tracker).
            include: When set, only matching endpoints are tracked (e.g. ``GET /predict``).
            exclude: Endpoints or URL prefixes to skip. Defaults to common docs and health routes.
            response_headers: Preset name, field list, field-to-header mapping, or boolean.
            include_emissions_header: Deprecated; equivalent to ``response_headers=True``.
            header_formatter: If set, builds response headers instead of ``response_headers``.
            task_name_formatter: Overrides default route-based task naming.
            on_request_complete: Optional callback
                ``(request, response, emissions_data | None, task_name)``.
            tracker_kwargs: Baseline kwargs merged into the tracker constructor.
            defer_measurement: Return the HTTP response before ``stop`` / ``stop_task``;
                skips response headers and runs ``on_request_complete`` in a background task.
            **emissions_tracker_kwargs: Additional :class:`~codecarbon.EmissionsTracker` kwargs.
        """
        super().__init__(app)
        self.project_name = project_name
        self.tracking_mode = tracking_mode
        self.defer_measurement = defer_measurement
        self.include = set(include) if include is not None else None
        self.exclude = set(exclude if exclude is not None else DEFAULT_EXCLUDE)
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
        if not should_track_request(request, self.include, self.exclude):
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

    def _create_and_start_tracker(self) -> EmissionsTracker:
        tracker = EmissionsTracker(
            project_name=self.project_name, **self.tracker_kwargs
        )
        tracker.start()
        return tracker

    async def _start_request_tracker(self) -> EmissionsTracker:
        return await asyncio.to_thread(self._create_and_start_tracker)

    async def _stop_request_tracker(
        self, tracker: EmissionsTracker
    ) -> EmissionsData | None:
        await asyncio.to_thread(tracker.stop)
        return getattr(tracker, "final_emissions_data", None)

    def _run_request_complete(
        self,
        request: Request,
        response: Response | None,
        emissions_data: EmissionsData | None,
    ) -> None:
        if self.on_request_complete is None or response is None:
            return
        task_name = build_task_name(request, self.task_name_formatter)
        self.on_request_complete(request, response, emissions_data, task_name)

    async def _finalize_request_measurement(
        self,
        tracker: EmissionsTracker,
        request: Request,
        response: Response | None,
    ) -> None:
        emissions_data = await self._stop_request_tracker(tracker)
        self._run_request_complete(request, response, emissions_data)

    async def _dispatch_request_mode(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        tracker = await self._start_request_tracker()
        response: Response | None = None
        try:
            response = await call_next(request)
        finally:
            if self.defer_measurement:
                asyncio.create_task(
                    self._finalize_request_measurement(tracker, request, response)
                )
            else:
                emissions_data = await self._stop_request_tracker(tracker)
                self._run_request_complete(request, response, emissions_data)
                self._apply_headers(response, emissions_data, request)
        return response

    async def _finalize_app_measurement(
        self,
        tracker: EmissionsTracker,
        task_name: str,
        request: Request,
        response: Response | None,
    ) -> None:
        async with self._measurement_lock:
            emissions_data = await asyncio.to_thread(tracker.stop_task, task_name)
        self._run_request_complete(request, response, emissions_data)

    async def _dispatch_app_mode(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        tracker = await self._get_app_tracker(request)
        task_name = build_task_name(request, self.task_name_formatter)
        response: Response | None = None
        emissions_data: EmissionsData | None = None
        if self.defer_measurement:
            async with self._measurement_lock:
                await asyncio.to_thread(tracker.start_task, task_name)
            try:
                response = await call_next(request)
            finally:
                asyncio.create_task(
                    self._finalize_app_measurement(
                        tracker, task_name, request, response
                    )
                )
            return response
        async with self._measurement_lock:
            await asyncio.to_thread(tracker.start_task, task_name)
            try:
                response = await call_next(request)
            finally:
                emissions_data = await asyncio.to_thread(tracker.stop_task, task_name)
        self._run_request_complete(request, response, emissions_data)
        self._apply_headers(response, emissions_data, request)
        return response

    async def _get_app_tracker(self, request: Request) -> EmissionsTracker:
        app_tracker = getattr(request.app.state, "codecarbon_tracker", None)
        if app_tracker is not None:
            return app_tracker
        if self._app_tracker is None:
            self._app_tracker = await asyncio.to_thread(self._create_and_start_tracker)
        return self._app_tracker


def add_codecarbon_middleware(app: Any, **kwargs: Any) -> None:
    """Register :class:`CodeCarbonMiddleware` on a FastAPI or Starlette app.

    Args:
        app: Application instance with ``add_middleware``.
        **kwargs: Forwarded to :class:`CodeCarbonMiddleware`.
    """
    app.add_middleware(CodeCarbonMiddleware, **kwargs)
