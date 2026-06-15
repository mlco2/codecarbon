"""FastAPI/Starlette middleware for per-request emissions tracking."""

from __future__ import annotations

import asyncio
import collections
import threading
from collections.abc import Awaitable, Callable, Iterable
from concurrent import futures
from typing import Any

from codecarbon.external.logger import logger

try:
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.types import ASGIApp, Message, Receive, Scope, Send
except ImportError as exc:
    raise ImportError(
        "CodeCarbon FastAPI integration requires Starlette (installed with FastAPI). "
        "Install optional dependencies with: pip install 'codecarbon[fastapi]'"
    ) from exc

from codecarbon import EmissionsTracker
from codecarbon.emissions_tracker import HttpRequestBaseline
from codecarbon.integrations.fastapi._routing import (
    DEFAULT_EXCLUDE,
    build_endpoint_key,
    should_track_request,
)
from codecarbon.output_methods.emissions_data import EmissionsData

DEFAULT_TRACKER_KWARGS: dict[str, Any] = {
    "save_to_file": False,
    "save_to_api": False,
    "save_to_logger": False,
}

_Job = tuple[Callable[..., Any], tuple[Any, ...], futures.Future[Any]]


class _TrackerRunner:
    """Single tracker thread: request-path jobs first, then pending finalization."""

    REQUEST = 0
    FINALIZE = 1

    def __init__(self, thread_name: str = "codecarbon-tracker") -> None:
        self._request_jobs: collections.deque[_Job] = collections.deque()
        self._finalize_jobs: collections.deque[_Job] = collections.deque()
        self._cond = threading.Condition()
        self._closed = False
        self._thread = threading.Thread(target=self._worker, name=thread_name, daemon=True)
        self._thread.start()

    def _run_job(self, job: _Job) -> None:
        func, args, future = job
        if future.cancelled():
            return
        try:
            future.set_result(func(*args))
        except Exception as exc:
            future.set_exception(exc)

    def _worker(self) -> None:
        while True:
            with self._cond:
                while (
                    not self._closed
                    and not self._request_jobs
                    and not self._finalize_jobs
                ):
                    self._cond.wait()
                if (
                    self._closed
                    and not self._request_jobs
                    and not self._finalize_jobs
                ):
                    return
                if self._request_jobs:
                    job = self._request_jobs.popleft()
                    lane = self.REQUEST
                else:
                    job = self._finalize_jobs.popleft()
                    lane = self.FINALIZE
            self._run_job(job)
            if lane == self.REQUEST:
                while True:
                    with self._cond:
                        if self._request_jobs:
                            break
                        if not self._finalize_jobs:
                            break
                        finalize_job = self._finalize_jobs.popleft()
                    self._run_job(finalize_job)

    def submit(
        self, lane: int, func: Callable[..., Any], *args: Any
    ) -> futures.Future[Any]:
        if self._closed:
            raise RuntimeError("cannot schedule tracker work after shutdown")
        future: futures.Future[Any] = futures.Future()
        job = (func, args, future)
        with self._cond:
            if lane == self.REQUEST:
                self._request_jobs.append(job)
            else:
                self._finalize_jobs.append(job)
            self._cond.notify()
        return future

    def submit_request(
        self, func: Callable[..., Any], *args: Any
    ) -> futures.Future[Any]:
        return self.submit(self.REQUEST, func, *args)

    async def run_async(
        self, lane: int, func: Callable[..., Any], *args: Any
    ) -> Any:
        return await asyncio.wrap_future(self.submit(lane, func, *args))

    def shutdown(self, *, wait: bool = True) -> None:
        if self._closed:
            return
        with self._cond:
            self._closed = True
            self._cond.notify_all()
        if wait:
            self._thread.join()


def log_request_complete(
    request: Request,
    response: Response,
    emissions_data: EmissionsData | None,
    task_name: str,
) -> None:
    """Default ``on_request_complete`` handler; logs via the ``codecarbon`` logger."""
    emissions = getattr(emissions_data, "emissions", None) if emissions_data else None
    logger.info(
        "CodeCarbon %s: emissions=%s kg CO2 status=%s",
        task_name,
        emissions,
        response.status_code,
    )


class CodeCarbonMiddleware:
    """ASGI middleware using a shared tracker and deferred per-request measurement."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        project_name: str = "codecarbon-fastapi",
        include: Iterable[str] | None = None,
        exclude: Iterable[str] | None = None,
        task_name_formatter: Callable[[Request], str] | None = None,
        on_request_complete: Callable[..., Any] | None = log_request_complete,
        tracker_kwargs: dict[str, Any] | None = None,
        **emissions_tracker_kwargs: Any,
    ) -> None:
        """Configure middleware.

        Args:
            app: Inner ASGI application.
            project_name: ``project_name`` passed to :class:`~codecarbon.EmissionsTracker`.
            include: When set, only matching endpoints are tracked (e.g. ``GET /predict``).
            exclude: Endpoints or URL prefixes to skip. Defaults to common docs and health routes.
            task_name_formatter: Overrides default route-based task naming.
            on_request_complete: Callback ``(request, response, emissions_data | None, task_name)``.
                Defaults to :func:`log_request_complete`; pass ``None`` to disable logging.
            tracker_kwargs: Baseline kwargs merged into the tracker constructor.
            **emissions_tracker_kwargs: Additional :class:`~codecarbon.EmissionsTracker` kwargs.
        """
        self.app = app
        self.project_name = project_name
        self.include = set(include) if include is not None else None
        self.exclude = set(exclude if exclude is not None else DEFAULT_EXCLUDE)
        self.task_name_formatter = task_name_formatter
        self.on_request_complete = on_request_complete
        merged: dict[str, Any] = dict(DEFAULT_TRACKER_KWARGS)
        merged.update(tracker_kwargs or {})
        merged.update(emissions_tracker_kwargs)
        merged.setdefault("allow_multiple_runs", True)
        self.tracker_kwargs = merged
        self._app_tracker: EmissionsTracker | None = None
        self._tracker_init_lock = threading.Lock()
        self._tracker_runner = _TrackerRunner()

    def shutdown_tracker_executor(self, *, wait: bool = True) -> None:
        """Shut down the tracker background thread (idempotent).

        Args:
            wait: When ``True``, block until queued tracker work finishes.
        """
        self._tracker_runner.shutdown(wait=wait)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI entrypoint."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        if not should_track_request(request, self.include, self.exclude):
            await self.app(scope, receive, send)
            return

        task_name = self._task_name(request)
        tracker, baseline = await asyncio.to_thread(
            self._begin_request, request, task_name
        )
        await self._handle_tracked(
            scope, receive, send, request, tracker, task_name, baseline
        )

    def _task_name(self, request: Request) -> str:
        if self.task_name_formatter is not None:
            return self.task_name_formatter(request)
        return build_endpoint_key(request)

    async def _run_request_tracker(
        self, func: Callable[..., Any], *args: Any
    ) -> Any:
        return await self._tracker_runner.run_async(_TrackerRunner.REQUEST, func, *args)

    async def _run_finalize_tracker(
        self, func: Callable[..., Any], *args: Any
    ) -> Any:
        return await self._tracker_runner.run_async(_TrackerRunner.FINALIZE, func, *args)

    def _create_and_start_tracker(self) -> EmissionsTracker:
        tracker = EmissionsTracker(
            project_name=self.project_name, **self.tracker_kwargs
        )
        tracker.start()
        return tracker

    def _lifespan_tracker(self, request: Request) -> EmissionsTracker | None:
        return getattr(request.app.state, "codecarbon_tracker", None)

    def _tracker_running(self, tracker: EmissionsTracker) -> bool:
        return getattr(tracker, "_start_time", None) is not None

    def _begin_request(
        self, request: Request, task_name: str
    ) -> tuple[EmissionsTracker, HttpRequestBaseline | None]:
        tracker = self._lifespan_tracker(request)
        if tracker is None:
            with self._tracker_init_lock:
                if self._app_tracker is None:
                    self._app_tracker = self._create_and_start_tracker()
                tracker = self._app_tracker
        if (
            self._lifespan_tracker(request) is not None
            and self._tracker_running(tracker)
        ):
            baseline = tracker.mark_http_request_start(task_name)
            return tracker, baseline
        tracker.start_task(task_name)
        return tracker, None

    def _finalize_on_worker(
        self,
        tracker: EmissionsTracker,
        task_name: str,
        request: Request,
        response: Response,
        run_callback: bool,
        baseline: HttpRequestBaseline | None,
    ) -> None:
        if baseline is not None:
            emissions_data = tracker.finish_http_request(baseline)
            resolved_task = baseline.task_name
        else:
            active_task = getattr(tracker, "_active_task", None)
            resolved_task = (
                active_task if isinstance(active_task, str) else task_name
            )
            emissions_data = tracker.stop_task(resolved_task)
        tracker.persist_completed_task(resolved_task)
        if run_callback:
            self._run_request_complete(
                request, response, emissions_data, resolved_task
            )

    def _run_request_complete(
        self,
        request: Request,
        response: Response | None,
        emissions_data: EmissionsData | None,
        task_name: str,
    ) -> None:
        if self.on_request_complete is None or response is None:
            return
        self.on_request_complete(request, response, emissions_data, task_name)

    def _schedule_finalize(self, coro: Awaitable[None]) -> None:
        async def _run() -> None:
            try:
                await coro
            except Exception:
                logger.exception("CodeCarbon deferred measurement failed")

        asyncio.create_task(_run())

    async def _finalize_after_response(
        self,
        tracker: EmissionsTracker,
        task_name: str,
        request: Request,
        response: Response,
        baseline: HttpRequestBaseline | None,
        *,
        run_callback: bool,
    ) -> None:
        await self._run_finalize_tracker(
            self._finalize_on_worker,
            tracker,
            task_name,
            request,
            response,
            run_callback,
            baseline,
        )

    async def _handle_tracked(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        request: Request,
        tracker: EmissionsTracker,
        task_name: str,
        baseline: HttpRequestBaseline | None,
    ) -> None:
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        error: BaseException | None = None
        try:
            await self.app(scope, receive, send_wrapper)
        except BaseException as exc:
            error = exc
        finally:
            response = Response(status_code=status_code)
            self._schedule_finalize(
                self._finalize_after_response(
                    tracker,
                    task_name,
                    request,
                    response,
                    baseline,
                    run_callback=error is None,
                )
            )
        if error is not None:
            raise error


def shutdown_codecarbon_middleware(app: Any, *, wait: bool = True) -> None:
    """Shut down the middleware tracker background thread registered on ``app``.

    Args:
        app: Application that called :func:`add_codecarbon_middleware`.
        wait: Passed to :meth:`CodeCarbonMiddleware.shutdown_tracker_executor`.
    """
    middleware = getattr(app.state, "codecarbon_middleware", None)
    if middleware is not None:
        middleware.shutdown_tracker_executor(wait=wait)


def add_codecarbon_middleware(app: Any, **kwargs: Any) -> None:
    """Register :class:`CodeCarbonMiddleware` on a FastAPI or Starlette app.

    Registers the instance on ``app.state.codecarbon_middleware`` so
    :func:`create_codecarbon_lifespan` or :func:`shutdown_codecarbon_middleware`
    can shut down the tracker background thread on teardown.

    Args:
        app: Application instance with ``add_middleware``.
        **kwargs: Forwarded to :class:`CodeCarbonMiddleware`.
    """
    registered: list[CodeCarbonMiddleware] = []

    class _RegisteredCodeCarbonMiddleware(CodeCarbonMiddleware):
        def __init__(self, asgi_app: ASGIApp, **kw: Any) -> None:
            super().__init__(asgi_app, **kw)
            registered.clear()
            registered.append(self)

    app.add_middleware(_RegisteredCodeCarbonMiddleware, **kwargs)
    app.build_middleware_stack()
    if registered:
        app.state.codecarbon_middleware = registered[0]
