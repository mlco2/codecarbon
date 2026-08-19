"""FastAPI/Starlette middleware for per-request emissions attribution."""

from __future__ import annotations

import functools
from collections.abc import Callable

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from codecarbon.emissions_tracker import BaseEmissionsTracker
from codecarbon.external.logger import logger
from codecarbon.integrations.fastapi.attribution import EnergyAttributor, RequestEnergy
from codecarbon.output_methods.emissions_data import EmissionsData


def log_request(
    energy: RequestEnergy, emissions: EmissionsData | None, status_code: int
) -> None:
    """Default ``on_request`` handler; logs via the ``codecarbon`` logger."""
    logger.info(
        "CodeCarbon %s: energy=%s kWh emissions=%s kg CO2 status=%s",
        energy.endpoint,
        energy.energy_kwh,
        getattr(emissions, "emissions", None),
        status_code,
    )


class CodeCarbonMiddleware:
    """Attributes a running tracker's energy to each HTTP request.

    A request's number is only known one or more sampling windows *after* its
    response was sent, so ``on_request`` is called then, from the tracker's
    scheduler thread. Keep it cheap and non-blocking.

    Args:
        app: Inner ASGI application.
        tracker: A tracker already started with ``tracker.start()``.
        on_request: Callback ``(RequestEnergy, EmissionsData | None, status_code)``.
            ``None`` disables reporting.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        tracker: BaseEmissionsTracker,
        on_request: (
            Callable[[RequestEnergy, EmissionsData | None, int], None] | None
        ) = log_request,
    ) -> None:
        self.app = app
        self.tracker = tracker
        self.on_request = on_request
        self.attributor = EnergyAttributor()
        self.attributor.reset_window(tracker._total_energy.kWh)
        tracker.add_energy_window_observer(self.attributor.on_window)

    def close(self) -> None:
        """Stop attributing and emit whatever is still in flight."""
        self.tracker.remove_energy_window_observer(self.attributor.on_window)
        self.attributor.close()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI entrypoint."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        state = self.attributor.begin(_endpoint(scope))
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # The route template only lands in the scope once Starlette's
            # router has run, so the endpoint can only be named here.
            state.endpoint = _endpoint(scope)
            state.on_resolved = functools.partial(self._resolved, status_code)
            self.attributor.end(state)

    def _resolved(self, status_code: int, energy: RequestEnergy) -> None:
        if self.on_request is None:
            return
        emissions = (
            self.tracker.http_request_emissions(energy.energy_kwh, energy.duration_s)
            if energy.energy_kwh is not None
            else None
        )
        self.on_request(energy, emissions, status_code)


def _endpoint(scope: Scope) -> str:
    route = scope.get("route")
    path = getattr(route, "path", None) or scope.get("path", "")
    return f"{scope.get('method', '')} {path}".strip()


def add_codecarbon_middleware(app, **kwargs) -> None:
    """Register :class:`CodeCarbonMiddleware` and expose it on ``app.state``.

    Starlette builds the middleware stack on startup, so the instance that
    actually serves requests is only knowable from inside its constructor.
    ``app.state.codecarbon_middleware.close()`` on shutdown.
    """

    class _Registered(CodeCarbonMiddleware):
        def __init__(self, asgi_app: ASGIApp, **kw) -> None:
            super().__init__(asgi_app, **kw)
            app.state.codecarbon_middleware = self

    app.add_middleware(_Registered, **kwargs)
