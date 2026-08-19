"""FastAPI/Starlette middleware for per-request emissions tracking."""

from __future__ import annotations

import asyncio
import dataclasses
import threading
from collections.abc import Awaitable, Callable, Iterable, Sequence
from concurrent import futures
from typing import Any

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from codecarbon import EmissionsTracker
from codecarbon.emissions_tracker import HttpRequestBaseline
from codecarbon.external.logger import logger
from codecarbon.integrations.fastapi._routing import (
    DEFAULT_EXCLUDE,
    build_endpoint_key,
    should_track_request,
)
from codecarbon.integrations.fastapi.tiers import (
    EndpointTotals,
    MeasurementTier,
    RequestMeasurement,
    TierDetection,
    detect_measurement_tier,
)
from codecarbon.output_methods.emissions_data import EmissionsData

DEFAULT_TRACKER_KWARGS: dict[str, Any] = {
    "save_to_file": False,
    "save_to_api": False,
    "save_to_logger": False,
}

# ponytail: local map only; full preset taxonomy if headers become a public API
_HEADER_UNITS: dict[str, str] = {
    "emissions": "kg",
    "emissions_rate": "kg-per-s",
    "duration": "s",
    "energy_consumed": "kwh",
    "cpu_energy": "kwh",
    "gpu_energy": "kwh",
    "ram_energy": "kwh",
    "cpu_power": "w",
    "gpu_power": "w",
    "ram_power": "w",
}


def _codecarbon_header_name(field: str) -> str:
    unit = _HEADER_UNITS.get(field, "")
    title = "-".join(part.capitalize() for part in field.split("_"))
    suffix = f"-{unit}" if unit else ""
    return f"X-CodeCarbon-{title}{suffix}"


def _resolve_header_fields(
    response_headers: bool | Sequence[str] | None,
) -> tuple[str, ...]:
    if not response_headers:
        return ()
    if response_headers is True:
        return ("emissions",)
    return tuple(response_headers)


def _inject_emission_headers(
    message: Message,
    measurement: RequestMeasurement | None,
    fields: Sequence[str],
) -> Message:
    """Add ``X-CodeCarbon-*`` headers.

    Headers are opt-in (``response_headers``); when enabled they always carry
    ``X-CodeCarbon-Tier`` next to the numbers, and report ``unavailable``
    rather than ``0`` when the backend cannot resolve the request.
    """
    if not fields or measurement is None:
        return message
    headers = list(message.get("headers", []))
    headers.append((b"X-CodeCarbon-Tier", measurement.tier.value.encode("latin-1")))
    emissions_data = measurement.emissions_data
    for field in fields:
        name = _codecarbon_header_name(field)
        if emissions_data is None:
            value = "unavailable"
        elif hasattr(emissions_data, field):
            value = str(getattr(emissions_data, field))
        else:
            continue
        headers.append((name.encode("latin-1"), value.encode("latin-1")))
    return {**message, "headers": headers}


def _carbon_intensity(tracker: EmissionsTracker | None) -> float:
    """Effective kg CO2 per kWh implied by the tracker's running totals."""
    total_energy = getattr(getattr(tracker, "_total_energy", None), "kWh", 0.0)
    total_emissions = getattr(tracker, "_total_emissions", 0.0)
    try:
        if total_energy and total_energy > 0:
            return float(total_emissions) / float(total_energy)
    except (TypeError, ValueError):
        pass
    return 0.0


def _estimate_from_duration(
    emissions_data: EmissionsData, intensity: float
) -> EmissionsData | None:
    """ESTIMATED tier: energy is analytic (``P x elapsed``) at any resolution.

    The sampled delta can still be 0 when the request fell between scheduler
    ticks; with a constant power model the honest figure is power x duration
    rather than 0. Returns ``None`` when carbon intensity is not yet known,
    so the caller reports unavailable instead of a zero.
    """
    duration = emissions_data.duration or 0.0
    if duration <= 0 or intensity <= 0:
        return None
    hours = duration / 3600.0
    cpu = (emissions_data.cpu_power or 0.0) / 1000.0 * hours
    gpu = (emissions_data.gpu_power or 0.0) / 1000.0 * hours
    ram = (emissions_data.ram_power or 0.0) / 1000.0 * hours
    energy = cpu + gpu + ram
    if energy <= 0:
        return None
    return dataclasses.replace(
        emissions_data,
        cpu_energy=cpu,
        gpu_energy=gpu,
        ram_energy=ram,
        energy_consumed=energy,
        emissions=energy * intensity,
        emissions_rate=energy * intensity / duration,
    )


def log_request_complete(
    request: Request,
    status_code: int,
    emissions_data: EmissionsData | None,
    task_name: str,
) -> None:
    """Default ``on_request_complete`` handler; logs via the ``codecarbon`` logger."""
    emissions = getattr(emissions_data, "emissions", None) if emissions_data else None
    logger.info(
        "CodeCarbon %s: emissions=%s kg CO2 status=%s",
        task_name,
        emissions,
        status_code,
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
        response_headers: bool | Sequence[str] | None = None,
        include_background_tasks: bool = True,
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
            on_request_complete: Callback ``(request, status_code, emissions_data | None, task_name)``.
                Defaults to :func:`log_request_complete`; pass ``None`` to disable logging.
            response_headers: When set, measure before ``http.response.start`` and inject
                ``X-CodeCarbon-*`` headers (``True`` → ``emissions`` only, or a field list).
                Adds sampling latency to the client response path.
            include_background_tasks: When ``True`` (default), finalize after the ASGI call
                returns so FastAPI/Starlette ``BackgroundTasks`` are included. When ``False``,
                finalize at end of response body (excludes post-body background work).
            tracker_kwargs: Baseline kwargs merged into the tracker constructor.
            **emissions_tracker_kwargs: Additional :class:`~codecarbon.EmissionsTracker` kwargs.
        """
        self.app = app
        self.project_name = project_name
        self.include = set(include) if include is not None else None
        self.exclude = set(exclude if exclude is not None else DEFAULT_EXCLUDE)
        self.task_name_formatter = task_name_formatter
        self.on_request_complete = on_request_complete
        self.header_fields = _resolve_header_fields(response_headers)
        self.include_background_tasks = include_background_tasks
        merged: dict[str, Any] = dict(DEFAULT_TRACKER_KWARGS)
        merged.update(tracker_kwargs or {})
        merged.update(emissions_tracker_kwargs)
        merged.setdefault("allow_multiple_runs", True)
        self.tracker_kwargs = merged
        self._app_tracker: EmissionsTracker | None = None
        self._tracker_init_lock = threading.Lock()
        # One worker: the tracker is not re-entrant, and requests must not block
        # on each other's measurement.
        self._tracker_runner = futures.ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="codecarbon-tracker"
        )
        # asyncio only keeps a weak reference to a running task.
        self._pending_finalizes: set[asyncio.Task[None]] = set()
        self._tier_detection: TierDetection | None = None
        self._totals: dict[str, EndpointTotals] = {}
        self._totals_lock = threading.Lock()

    @property
    def measurement_tier(self) -> MeasurementTier | None:
        """Tier resolved from the tracker's hardware, or ``None`` before first use."""
        return None if self._tier_detection is None else self._tier_detection.tier

    @property
    def tier_detection(self) -> TierDetection | None:
        """Full detection result (overall tier plus per-component tiers)."""
        return self._tier_detection

    def endpoint_totals(self) -> dict[str, EndpointTotals]:
        """Per-endpoint aggregates. The only energy output in AGGREGATE_ONLY.

        Idle/baseline power is charged to requests, not subtracted, so these
        totals sum to the tracker total.
        """
        with self._totals_lock:
            return {
                key: dataclasses.replace(value) for key, value in self._totals.items()
            }

    def _resolve_tier(self, tracker: EmissionsTracker) -> TierDetection:
        """Resolve the tier once, from the hardware the tracker actually detected."""
        detection = self._tier_detection
        if detection is None:
            detection = detect_measurement_tier(getattr(tracker, "_hardware", None))
            self._tier_detection = detection
            logger.debug("CodeCarbon measurement tier: %s", detection.describe())
        return detection

    def _build_measurement(
        self,
        detection: TierDetection,
        endpoint: str,
        task_name: str,
        emissions_data: EmissionsData | None,
        tracker: EmissionsTracker | None = None,
    ) -> RequestMeasurement:
        tier = detection.tier
        duration = float(getattr(emissions_data, "duration", 0.0) or 0.0)
        if emissions_data is None:
            return RequestMeasurement(
                tier, task_name, endpoint, duration, None, "no measurement returned"
            )
        if tier is MeasurementTier.AGGREGATE_ONLY:
            return RequestMeasurement(
                tier,
                task_name,
                endpoint,
                duration,
                None,
                "backend resolution is coarser than a request; use endpoint_totals()",
            )
        if tier is MeasurementTier.ESTIMATED and not emissions_data.energy_consumed:
            emissions_data = _estimate_from_duration(
                emissions_data, _carbon_intensity(tracker)
            )
        if emissions_data is None or not emissions_data.energy_consumed:
            return RequestMeasurement(
                tier,
                task_name,
                endpoint,
                duration,
                None,
                "request spanned no completed sampling window",
            )
        return RequestMeasurement(tier, task_name, endpoint, duration, emissions_data)

    def _record_totals(
        self,
        detection: TierDetection,
        endpoint: str,
        emissions_data: EmissionsData | None,
    ) -> None:
        with self._totals_lock:
            totals = self._totals.get(endpoint)
            if totals is None:
                totals = EndpointTotals(endpoint=endpoint, tier=detection.tier)
                self._totals[endpoint] = totals
            totals.add(emissions_data)

    def shutdown_tracker_executor(self, *, wait: bool = True) -> None:
        """Shut down the tracker background thread (idempotent).

        Also stops the tracker this middleware created itself (the lazy path,
        used when there is no ``create_codecarbon_lifespan``). A lifespan
        tracker is owned by the lifespan and is left alone.

        Args:
            wait: When ``True``, block until queued tracker work finishes.
        """
        self._tracker_runner.shutdown(wait=wait)
        tracker, self._app_tracker = self._app_tracker, None
        if tracker is not None:
            tracker.stop()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI entrypoint."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        if not should_track_request(request, self.include, self.exclude):
            await self.app(scope, receive, send)
            return

        tracker, baseline = await self._run_begin_request(request)
        await self._handle_tracked(scope, receive, send, request, tracker, baseline)

    def _task_name(self, request: Request) -> str:
        if self.task_name_formatter is not None:
            return self.task_name_formatter(request)
        return build_endpoint_key(request)

    async def _run_on_tracker(self, func: Callable[..., Any], *args: Any) -> Any:
        return await asyncio.wrap_future(self._tracker_runner.submit(func, *args))

    async def _run_begin_request(
        self, request: Request
    ) -> tuple[EmissionsTracker, HttpRequestBaseline]:
        return await self._run_on_tracker(self._begin_request, request)

    def _create_and_start_tracker(self) -> EmissionsTracker:
        tracker = EmissionsTracker(
            project_name=self.project_name, **self.tracker_kwargs
        )
        tracker.start()
        return tracker

    def _lifespan_tracker(self, request: Request) -> EmissionsTracker | None:
        return getattr(request.app.state, "codecarbon_tracker", None)

    def _begin_request(
        self, request: Request
    ) -> tuple[EmissionsTracker, HttpRequestBaseline]:
        tracker = self._lifespan_tracker(request)
        if tracker is None:
            with self._tracker_init_lock:
                if self._app_tracker is None:
                    self._app_tracker = self._create_and_start_tracker()
                tracker = self._app_tracker
        # mark_http_request_start raises when the tracker was never started;
        # start_task is not a usable fallback because it stops the scheduler and
        # overwrites the single _active_task slot shared by concurrent requests.
        return tracker, tracker.mark_http_request_start("")

    def _finalize_on_worker(
        self,
        tracker: EmissionsTracker,
        request: Request,
        status_code: int,
        run_callback: bool,
        baseline: HttpRequestBaseline,
    ) -> RequestMeasurement:
        detection = self._resolve_tier(tracker)
        # The route template only lands in request.scope once Starlette's router
        # has run, so the task can only be named here, not at request start.
        task_name = self._task_name(request)
        emissions_data = tracker.finish_http_request(baseline, task_name)
        tracker.persist_completed_task(baseline.task_name)
        tracker.discard_task(baseline.task_name)
        self._record_totals(detection, task_name, emissions_data)
        measurement = self._build_measurement(
            detection, task_name, baseline.task_name, emissions_data, tracker
        )
        try:
            request.state.codecarbon = measurement
        except Exception:  # pragma: no cover - exotic scopes without state
            logger.debug("CodeCarbon: could not attach measurement to request.state")
        if run_callback:
            self._run_request_complete(
                request, status_code, measurement.emissions_data, task_name
            )
        return measurement

    def _run_request_complete(
        self,
        request: Request,
        status_code: int,
        emissions_data: EmissionsData | None,
        task_name: str,
    ) -> None:
        if self.on_request_complete is None:
            return
        self.on_request_complete(request, status_code, emissions_data, task_name)

    def _schedule_finalize(self, coro: Awaitable[None]) -> None:
        async def _run() -> None:
            try:
                await coro
            except Exception:
                logger.exception("CodeCarbon deferred measurement failed")

        task = asyncio.create_task(_run())
        self._pending_finalizes.add(task)
        task.add_done_callback(self._pending_finalizes.discard)

    async def _finalize_after_response(
        self,
        tracker: EmissionsTracker,
        request: Request,
        status_code: int,
        baseline: HttpRequestBaseline,
        *,
        run_callback: bool,
    ) -> RequestMeasurement:
        return await self._run_on_tracker(
            self._finalize_on_worker,
            tracker,
            request,
            status_code,
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
        baseline: HttpRequestBaseline,
    ) -> None:
        if self.header_fields:
            await self._handle_tracked_sync_headers(
                scope, receive, send, request, tracker, baseline
            )
            return
        if self.include_background_tasks:
            await self._handle_tracked_after_app(
                scope, receive, send, request, tracker, baseline
            )
            return
        await self._handle_tracked_end_of_body(
            scope, receive, send, request, tracker, baseline
        )

    async def _handle_tracked_after_app(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        request: Request,
        tracker: EmissionsTracker,
        baseline: HttpRequestBaseline,
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
            self._schedule_finalize(
                self._finalize_after_response(
                    tracker,
                    request,
                    status_code,
                    baseline,
                    run_callback=error is None,
                )
            )
        if error is not None:
            raise error

    async def _handle_tracked_end_of_body(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        request: Request,
        tracker: EmissionsTracker,
        baseline: HttpRequestBaseline,
    ) -> None:
        status_code = 500
        finalized = False

        def _kick_finalize(*, run_callback: bool) -> None:
            nonlocal finalized
            if finalized:
                return
            finalized = True
            self._schedule_finalize(
                self._finalize_after_response(
                    tracker,
                    request,
                    status_code,
                    baseline,
                    run_callback=run_callback,
                )
            )

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
            if message["type"] == "http.response.body" and not message.get(
                "more_body", False
            ):
                _kick_finalize(run_callback=True)

        error: BaseException | None = None
        try:
            await self.app(scope, receive, send_wrapper)
        except BaseException as exc:
            error = exc
        finally:
            _kick_finalize(run_callback=error is None)
        if error is not None:
            raise error

    async def _handle_tracked_sync_headers(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        request: Request,
        tracker: EmissionsTracker,
        baseline: HttpRequestBaseline,
    ) -> None:
        status_code = 500
        finalized = False

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code, finalized
            if message["type"] != "http.response.start":
                await send(message)
                return
            status_code = message["status"]
            measurement = await self._finalize_after_response(
                tracker,
                request,
                status_code,
                baseline,
                run_callback=True,
            )
            finalized = True
            await send(
                _inject_emission_headers(message, measurement, self.header_fields)
            )

        error: BaseException | None = None
        try:
            await self.app(scope, receive, send_wrapper)
        except BaseException as exc:
            error = exc
        finally:
            if not finalized:
                self._schedule_finalize(
                    self._finalize_after_response(
                        tracker,
                        request,
                        status_code,
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

    class _RegisteredCodeCarbonMiddleware(CodeCarbonMiddleware):
        def __init__(self, asgi_app: ASGIApp, **kw: Any) -> None:
            super().__init__(asgi_app, **kw)
            # Starlette rebuilds the middleware stack on startup, so point
            # app.state at whichever instance actually serves requests.
            # Otherwise shutdown targets a stale instance and never stops the
            # lazily created tracker.
            app.state.codecarbon_middleware = self

    app.add_middleware(_RegisteredCodeCarbonMiddleware, **kwargs)
