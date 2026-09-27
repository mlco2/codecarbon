"""FastAPI/Starlette middleware for per-request emissions attribution."""

from __future__ import annotations

import functools
import threading
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any

try:
    import anyio.to_thread
    from starlette.types import ASGIApp, Message, Receive, Scope, Send
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "The CodeCarbon FastAPI integration needs FastAPI/Starlette: "
        "pip install 'codecarbon[fastapi]'"
    ) from e

from codecarbon.emissions_tracker import BaseEmissionsTracker, WindowSample
from codecarbon.external.logger import logger
from codecarbon.integrations.fastapi.attribution import (
    EnergyAttributor,
    RequestEnergy,
    _Meter,
    _Metered,
)

#: The meter of the request whose task (or child task) is running, if any.
_current_meter: ContextVar[_Meter | None] = ContextVar(
    "codecarbon_request_meter", default=None
)
_patch_lock = threading.Lock()
_patch_users = 0
#: Whether ``_metered_run_sync`` is reachable from ``anyio.to_thread.run_sync``.
_patch_in_chain = False
_original_run_sync: Callable[..., Any] = anyio.to_thread.run_sync


async def _metered_run_sync(func: Callable[..., Any], *args: Any, **kwargs: Any):
    """``anyio.to_thread.run_sync`` that meters the call for the current request.

    Starlette and FastAPI send sync endpoints, sync dependencies, sync
    iterators and file work through it. Outside a metered request it calls
    the original unchanged.
    """
    meter = _current_meter.get()
    if meter is not None:
        func = functools.partial(meter.run_in_thread, func)
    return await _original_run_sync(func, *args, **kwargs)


def _patch_run_sync() -> None:
    """Route ``anyio.to_thread.run_sync`` through the meter. Reference-counted."""
    global _patch_users, _patch_in_chain, _original_run_sync
    with _patch_lock:
        if not _patch_in_chain:
            _original_run_sync = anyio.to_thread.run_sync
            anyio.to_thread.run_sync = _metered_run_sync
            _patch_in_chain = True
        _patch_users += 1


def _unpatch_run_sync() -> None:
    """Undo :func:`_patch_run_sync` once its last user is gone.

    If someone patched ``run_sync`` on top of ours, ours stays in their chain
    (it does nothing outside a metered request) rather than breaking it.
    """
    global _patch_users, _patch_in_chain
    with _patch_lock:
        _patch_users -= 1
        if _patch_users == 0 and anyio.to_thread.run_sync is _metered_run_sync:
            anyio.to_thread.run_sync = _original_run_sync
            _patch_in_chain = False


def log_request(
    energy: RequestEnergy, emissions_kg: float | None, status_code: int
) -> None:
    """Default ``on_request`` handler; logs via the ``codecarbon`` logger."""
    logger.debug(
        "CodeCarbon %s: cpu=%s kWh gpu=%s kWh emissions=%s kg CO2 status=%s",
        energy.endpoint,
        energy.energy_kwh,
        energy.gpu_kwh,
        emissions_kg,
        status_code,
    )


class CodeCarbonMiddleware:
    """Attributes a running tracker's energy to each HTTP request.

    Add it at module level with ``app.add_middleware(CodeCarbonMiddleware)``.
    The tracker is either passed as ``tracker=`` or looked up per request from
    ``app.state.codecarbon_tracker``, so it can be created and started in the
    app's lifespan. Requests are only recorded while that tracker is running.

    A request's number is only known one or more sampling windows *after* its
    response was sent, so ``on_request`` is called then, from the tracker's
    scheduler thread. Keep it cheap and non-blocking.

    Args:
        app: Inner ASGI application.
        tracker: Optional tracker; defaults to ``app.state.codecarbon_tracker``.
        on_request: Callback ``(RequestEnergy, emissions_kg | None, status_code)``.
            ``None`` disables reporting.
        meter_threadpool: Also meter the CPU time of work a request sends to
            the threadpool (sync endpoints and dependencies, sync iterators).
            This wraps ``anyio.to_thread.run_sync`` process-wide while a
            tracker is attached; outside a request it behaves as before.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        tracker: BaseEmissionsTracker | None = None,
        on_request: (
            Callable[[RequestEnergy, float | None, int], None] | None
        ) = log_request,
        meter_threadpool: bool = True,
    ) -> None:
        self.app = app
        self.meter_threadpool = meter_threadpool
        self._patched = False
        self.tracker = tracker
        self.on_request = on_request
        self.attributor = EnergyAttributor()
        self._attached: BaseEmissionsTracker | None = None
        # kg CO2eq per kWh, refreshed once per sampling window.
        self._intensity: float | None = None

    def close(self) -> None:
        """Stop attributing and emit whatever is still in flight.

        Called automatically on lifespan shutdown.
        """
        if self._attached is not None:
            self._attached.remove_energy_window_observer(self._on_window)
            self._attached = None
        if self._patched:
            _unpatch_run_sync()
            self._patched = False
        self.attributor.close()

    def _on_window(self, sample: WindowSample) -> None:
        # Scheduler thread: one intensity lookup per window, not per request.
        try:
            self._intensity = self._attached._carbon_intensity_kg_per_kwh()
        except Exception:
            logger.debug("CodeCarbon: carbon intensity unavailable", exc_info=True)
        self.attributor.on_window(sample)

    def _running_tracker(self, scope: Scope) -> BaseEmissionsTracker | None:
        tracker = self.tracker
        if tracker is None and "app" in scope:
            tracker = getattr(scope["app"].state, "codecarbon_tracker", None)
        if tracker is None or tracker._start_time is None:
            return None
        return tracker

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI entrypoint."""
        if scope["type"] == "lifespan":

            async def lifespan_send(message: Message) -> None:
                if message["type"] == "lifespan.shutdown.complete":
                    self.close()
                await send(message)

            await self.app(scope, receive, lifespan_send)
            return

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        tracker = self._running_tracker(scope)
        if tracker is not self._attached:
            # Tracker stopped, replaced or first seen: settle what we hold.
            self.close()
            if tracker is not None:
                self.attributor.reset_window(tracker._window_sample())
                tracker.add_energy_window_observer(self._on_window)
                self._attached = tracker
                if self.meter_threadpool:
                    _patch_run_sync()
                    self._patched = True
        if tracker is None:
            await self.app(scope, receive, send)
            return

        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        meter = _Meter()
        state = self.attributor.begin(_endpoint(scope), meter)
        token = _current_meter.set(meter) if self._patched else None
        try:
            await _Metered(self.app(scope, receive, send_wrapper), meter)
        finally:
            if token is not None:
                _current_meter.reset(token)
            # The route template only lands in the scope once Starlette's
            # router has run, so the endpoint can only be named here.
            state.endpoint = _endpoint(scope)
            state.on_resolved = functools.partial(self._resolved, status_code)
            self.attributor.end(state)

    def _resolved(self, status_code: int, energy: RequestEnergy) -> None:
        if self.on_request is None:
            return
        emissions_kg = (
            (energy.energy_kwh + energy.gpu_kwh) * self._intensity
            if energy.energy_kwh is not None and self._intensity is not None
            else None
        )
        self.on_request(energy, emissions_kg, status_code)


def _endpoint(scope: Scope) -> str:
    route = scope.get("route")
    path = getattr(route, "path", None) or scope.get("path", "")
    return f"{scope.get('method', '')} {path}".strip()
