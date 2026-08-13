"""Fair-share per-request energy attribution.

Each completed sampling window ``(t_prev, t_now, dE)`` is split across the
requests that were in flight during it, weighted by their overlap with the
window and normalised **by the sum of the weights**. Windows with nothing in
flight go entirely to ``unattributed_kwh``. The invariant is::

    sum(per-request energy) + unattributed == run total

exactly, at every window. That is the property :mod:`tests` pins down.

This replaces "snapshot the cumulative counters at request start and again at
request end", which counts the same joules once per concurrent request: the
overcount factor is the concurrency (3.6x at 4 in flight, 88x at 100).

What it is not
--------------
Attribution is *allocation*, not measurement. With the default ``wall``
weighting a request that sleeps for a second and a request that burns a core
for a second receive the same share, because they occupied the same second of
the machine. That is a cost-allocation answer, and it is the honest one when
nothing tells you which request caused which watt. ``cpu`` weighting (opt-in,
see :func:`install_cpu_accounting`) separates them by charging each request the
on-thread CPU time its asyncio task actually burned.
"""

from __future__ import annotations

import asyncio
import contextvars
import statistics
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Optional

from codecarbon.external.logger import logger

WEIGHTINGS = ("wall", "cpu")

#: Quality tiers. ``unresolved`` carries no energy number at all - the request
#: never covered a completed sampling window, and zero would be a lie.
UNRESOLVED = "unresolved"
INTERPOLATED = "interpolated"
MEASURED = "measured"

# How many idle windows to keep for the baseline median. Bounded on purpose:
# a long-lived server must not grow a list forever, and a recent median also
# tracks drift in the machine's idle draw.
_IDLE_SAMPLES = 256

_current: contextvars.ContextVar[Optional["_InFlight"]] = contextvars.ContextVar(
    "codecarbon_request", default=None
)


# --- per-task CPU accounting -------------------------------------------------


class _TimedCoro:
    """Charge each resumption's thread CPU time to the owning request."""

    __slots__ = ("_coro", "_acc")

    def __init__(self, coro: Any, acc: list) -> None:
        self._coro = coro
        self._acc = acc

    def send(self, value: Any) -> Any:
        mark = time.thread_time()
        try:
            return self._coro.send(value)
        finally:
            self._acc[0] += time.thread_time() - mark

    def throw(self, *args: Any, **kwargs: Any) -> Any:
        mark = time.thread_time()
        try:
            return self._coro.throw(*args, **kwargs)
        finally:
            self._acc[0] += time.thread_time() - mark

    def close(self) -> Any:
        return self._coro.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._coro, name)

    def __await__(self) -> Any:
        return self._coro.__await__()


def install_cpu_accounting(loop: asyncio.AbstractEventLoop | None = None) -> None:
    """Install an asyncio task factory that charges CPU time to the request.

    Required for ``weighting="cpu"``. Replaces the loop's task factory, so it
    is incompatible with another library that sets one. Measured cost:
    ~2 us per ``create_task``, ~47 us per request end to end.

    Args:
        loop: Event loop to instrument. Defaults to the running loop.
    """
    loop = loop or asyncio.get_event_loop()

    def factory(loop: Any, coro: Any, **kwargs: Any) -> asyncio.Task:
        state = _current.get()
        if state is not None:
            coro = _TimedCoro(coro, state.cpu_acc)
        return asyncio.Task(coro, loop=loop, **kwargs)

    loop.set_task_factory(factory)


# --- results -----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RequestEnergy:
    """One request's finished attribution, with the caveats attached.

    ``energy_kwh`` is the *marginal* share: the part of the window's energy
    above the idle baseline, when a baseline was subtracted. ``baseline_share_kwh``
    is this request's per-capita cut of the energy the machine would have burned
    anyway. They are reported separately because they answer different
    questions: marginal energy is stable against traffic volume, allocated
    energy (``energy_kwh + baseline_share_kwh``) accounts for the whole machine.

    There is deliberately no +/- error bar. The dominant error here is the
    assumption that overlap tracks causation, and that has no distribution to
    quote.
    """

    endpoint: str
    quality: str
    #: ``None`` when ``quality == "unresolved"``.
    energy_kwh: float | None
    baseline_share_kwh: float | None
    duration_s: float
    #: Completed sampling windows this request overlapped.
    windows: int
    #: Mean number of requests it competed against, window-weighted.
    mean_concurrency: float | None
    cpu_seconds: float
    weighting: str
    baseline_subtracted: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable view."""
        return {
            "endpoint": self.endpoint,
            "quality": self.quality,
            "energy_kwh": self.energy_kwh,
            "baseline_share_kwh": self.baseline_share_kwh,
            "duration_s": self.duration_s,
            "windows": self.windows,
            "mean_concurrency": self.mean_concurrency,
            "cpu_seconds": self.cpu_seconds,
            "weighting": self.weighting,
            "baseline_subtracted": self.baseline_subtracted,
        }


@dataclass(slots=True)
class EndpointEnergy:
    """Aggregate for one endpoint. This is the number worth reporting.

    Individual per-request shares of sub-interval requests are dominated by
    where the request happened to fall relative to the sampling window: 400
    sequential 5 ms calls measured shares spanning 0.028-0.812 uWh (236% RSD)
    while this aggregate was a stable 0.043 uWh/call.
    """

    endpoint: str
    count: int = 0
    energy_kwh: float = 0.0
    baseline_share_kwh: float = 0.0
    quality: dict[str, int] = field(default_factory=dict)

    @property
    def mean_energy_kwh(self) -> float | None:
        """Mean marginal energy over the calls that produced a number."""
        resolved = self.count - self.quality.get(UNRESOLVED, 0)
        return self.energy_kwh / resolved if resolved else None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable view."""
        return {
            "endpoint": self.endpoint,
            "count": self.count,
            "energy_kwh": self.energy_kwh,
            "baseline_share_kwh": self.baseline_share_kwh,
            "mean_energy_kwh": self.mean_energy_kwh,
            "quality": dict(self.quality),
        }


@dataclass(slots=True)
class _InFlight:
    """Mutable per-request state. ~370 B, freed as soon as the request emits."""

    endpoint: str
    start: float
    end: float | None = None
    energy: float = 0.0
    baseline_share: float = 0.0
    windows: int = 0
    overlap_s: float = 0.0
    cpu_s: float = 0.0
    concurrency_sum: float = 0.0
    baseline_seen: bool = False
    cpu_acc: list = field(default_factory=lambda: [0.0])
    cpu_mark: float = 0.0


# --- attributor --------------------------------------------------------------


class EnergyAttributor:
    """Splits each sampling window's energy across the requests in flight.

    Args:
        weighting: ``"wall"`` (default) weights by overlap with the window -
            cost allocation. ``"cpu"`` weights by on-thread CPU time and
            requires :func:`install_cpu_accounting`.
        cores: CPU-seconds of capacity per second of wall clock, used to
            normalise ``cpu`` weights. ``1`` encodes "one event-loop thread",
            which is right for a plain async app. Raise it if request handlers
            fan out to ``run_in_executor`` or a thread pool, otherwise a window
            in which everyone used 1 ms of CPU hands that 1 ms the whole
            window's energy.
        subtract_baseline: Split each window into ``P_idle * width`` and a
            dynamic remainder, share only the remainder, and record each
            request's per-capita cut of the baseline separately. ``P_idle`` is
            the median power over windows with nothing in flight. If the server
            never idles there is no sample, nothing is subtracted, and every
            result carries ``baseline_subtracted=False``. Nameplate TDP is not
            used as a fallback: a wrong baseline subtracts a fixed amount from
            every request and drives short requests negative.
        on_request: Called with each :class:`RequestEnergy` as it resolves,
            one or more windows *after* the response was sent.
        track_endpoints: Keep :class:`EndpointEnergy` aggregates (default).
    """

    def __init__(
        self,
        *,
        weighting: str = "wall",
        cores: float = 1.0,
        subtract_baseline: bool = False,
        on_request: Callable[[RequestEnergy], None] | None = None,
        track_endpoints: bool = True,
    ) -> None:
        if weighting not in WEIGHTINGS:
            raise ValueError(
                f"weighting must be one of {WEIGHTINGS}, got {weighting!r}"
            )
        if cores <= 0:
            raise ValueError(f"cores must be > 0, got {cores!r}")
        self.weighting = weighting
        self.cores = cores
        self.subtract_baseline = subtract_baseline
        self.on_request = on_request
        self.track_endpoints = track_endpoints

        self._in_flight: dict[int, _InFlight] = {}
        self.endpoints: dict[str, EndpointEnergy] = {}
        #: Running sum of everything handed to requests, kWh.
        self.attributed_kwh = 0.0
        #: Idle windows plus every subtracted baseline, kWh.
        self.unattributed_kwh = 0.0
        #: Energy actually taken in from closed windows. ``attributed_kwh +
        #: unattributed_kwh == settled_kwh`` holds exactly after every window;
        #: it is below the tracker's run total by whatever a wrapped counter
        #: dropped (``windows_skipped``) plus the final unsampled partial window.
        self.settled_kwh = 0.0
        self.windows_settled = 0
        #: Windows where the energy counter went backwards (RAPL wrap/reset).
        self.windows_skipped = 0
        self._idle_power_w: deque[float] = deque(maxlen=_IDLE_SAMPLES)
        self._t_prev = time.perf_counter()
        self._e_prev = 0.0

    # -- lifecycle ------------------------------------------------------------

    def reset_window(self, total_energy_kwh: float = 0.0) -> None:
        """Anchor the first window at now. Call when the tracker starts."""
        self._t_prev = time.perf_counter()
        self._e_prev = total_energy_kwh

    def begin(self, endpoint: str) -> _InFlight:
        """Start weighting a request. Returns the handle to pass to :meth:`end`."""
        state = _InFlight(endpoint=endpoint, start=time.perf_counter())
        self._in_flight[id(state)] = state
        if self.weighting == "cpu":
            _current.set(state)
        return state

    def end(self, state: _InFlight) -> None:
        """Stamp the request finished.

        Deliberately does **not** settle. The request stays weighted until the
        next real sample closes, because at response time the machine's power
        over the last partial window is genuinely unknown - settling here would
        drop that energy into a zero-width window and silently lose it.
        """
        state.end = time.perf_counter()

    def close(self) -> None:
        """Emit every in-flight request as-is. Call after the tracker stops.

        Requests that never covered a window come out ``unresolved``.
        """
        for state in list(self._in_flight.values()):
            self._emit(state)
        self._in_flight.clear()
        if self.weighting == "cpu":
            _current.set(None)

    # -- window settlement ----------------------------------------------------

    def on_window(self, total_energy_kwh: float) -> None:
        """Close a sampling window with the tracker's cumulative energy.

        Wired to :meth:`~codecarbon.emissions_tracker.BaseEmissionsTracker.add_energy_window_observer`.
        Only ever called from a real hardware sample.
        """
        self._settle(total_energy_kwh)
        now = time.perf_counter()
        for key, state in list(self._in_flight.items()):
            if state.end is not None and state.end <= now:
                del self._in_flight[key]
                self._emit(state)

    def _settle(self, total_energy_kwh: float) -> None:
        now = time.perf_counter()
        w0, w1 = self._t_prev, now
        width = w1 - w0
        delta = total_energy_kwh - self._e_prev
        self._t_prev, self._e_prev = now, total_energy_kwh
        if width <= 0:
            return
        if delta < 0:
            # Counter wraparound or reset: no honest way to split a negative.
            self.windows_skipped += 1
            return
        self.windows_settled += 1
        self.settled_kwh += delta

        states: list[_InFlight] = []
        weights: list[float] = []
        for state in self._in_flight.values():
            lo = max(state.start, w0)
            hi = min(state.end if state.end is not None else w1, w1)
            overlap = hi - lo
            if overlap <= 0:
                continue
            if self.weighting == "cpu":
                cpu = state.cpu_acc[0] - state.cpu_mark
                state.cpu_mark = state.cpu_acc[0]
                state.cpu_s += cpu
                weights.append(max(0.0, cpu))
            else:
                weights.append(overlap)
            state.overlap_s += overlap
            states.append(state)

        count = len(states)
        if count == 0:
            # Nothing in flight: this window is the machine idling.
            self._idle_power_w.append(delta * 3.6e6 / width)
            self.unattributed_kwh += delta
            return

        total_weight = sum(weights)
        if total_weight <= 0:
            # cpu weighting, nobody on-CPU: this is idle energy, not request
            # energy. Splitting it evenly would invent work that never ran.
            self._idle_power_w.append(delta * 3.6e6 / width)
            self.unattributed_kwh += delta
            for state in states:
                state.windows += 1
                state.concurrency_sum += count
            return

        baseline_w = self.baseline_watts() if self.subtract_baseline else None
        base = min(delta, baseline_w * width / 3.6e6) if baseline_w else 0.0
        dynamic = delta - base
        self.unattributed_kwh += base

        if self.weighting == "cpu":
            # Physical reading: energy per CPU-second. The window's capacity is
            # width * cores; CPU time nobody claimed stays unattributed rather
            # than inflating whoever did run.
            capacity = max(width * self.cores, total_weight)
            self.unattributed_kwh += dynamic * (1.0 - total_weight / capacity)
            dynamic *= total_weight / capacity

        for state, weight in zip(states, weights):
            share = dynamic * (weight / total_weight)
            state.energy += share
            state.baseline_share += base / count
            state.baseline_seen = state.baseline_seen or baseline_w is not None
            state.windows += 1
            state.concurrency_sum += count
            self.attributed_kwh += share

    # -- reporting ------------------------------------------------------------

    def baseline_watts(self) -> float | None:
        """Median power over recent idle windows, or ``None`` if never idle."""
        if not self._idle_power_w:
            return None
        return statistics.median(self._idle_power_w)

    def _emit(self, state: _InFlight) -> None:
        if state.windows == 0:
            quality = UNRESOLVED
        elif state.windows < 2:
            quality = INTERPOLATED
        else:
            quality = MEASURED
        resolved = quality != UNRESOLVED
        result = RequestEnergy(
            endpoint=state.endpoint,
            quality=quality,
            energy_kwh=state.energy if resolved else None,
            baseline_share_kwh=state.baseline_share if resolved else None,
            duration_s=(state.end or time.perf_counter()) - state.start,
            windows=state.windows,
            mean_concurrency=(
                state.concurrency_sum / state.windows if state.windows else None
            ),
            cpu_seconds=state.cpu_s,
            weighting=self.weighting,
            baseline_subtracted=state.baseline_seen,
        )
        if self.track_endpoints:
            agg = self.endpoints.get(state.endpoint)
            if agg is None:
                agg = self.endpoints[state.endpoint] = EndpointEnergy(state.endpoint)
            agg.count += 1
            agg.energy_kwh += state.energy
            agg.baseline_share_kwh += state.baseline_share
            agg.quality[quality] = agg.quality.get(quality, 0) + 1
        if self.on_request is not None:
            try:
                self.on_request(result)
            except Exception:
                logger.exception("CodeCarbon attribution callback failed")

    def report(self) -> dict[str, Any]:
        """Per-endpoint aggregates plus the run-level accounting."""
        return {
            "weighting": self.weighting,
            "endpoints": {k: v.to_dict() for k, v in self.endpoints.items()},
            "attributed_kwh": self.attributed_kwh,
            "unattributed_kwh": self.unattributed_kwh,
            "total_kwh": self.attributed_kwh + self.unattributed_kwh,
            "settled_kwh": self.settled_kwh,
            "baseline_watts": self.baseline_watts(),
            "windows_settled": self.windows_settled,
            "windows_skipped": self.windows_skipped,
            "in_flight": len(self._in_flight),
        }
