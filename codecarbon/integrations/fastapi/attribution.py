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
Attribution is *allocation*, not measurement. A request that sleeps for a second
and a request that burns a core for a second receive the same share, because
they occupied the same second of the machine. That is a cost-allocation answer, and it is the honest one when
nothing tells you which request caused which watt.
"""

from __future__ import annotations

import statistics
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

from codecarbon.external.logger import logger

#: Quality tiers. ``unresolved`` carries no energy number at all - the request
#: never covered a completed sampling window, and zero would be a lie.
UNRESOLVED = "unresolved"
INTERPOLATED = "interpolated"
MEASURED = "measured"

# How many idle windows to keep for the baseline median. Bounded on purpose:
# a long-lived server must not grow a list forever, and a recent median also
# tracks drift in the machine's idle draw.
_IDLE_SAMPLES = 256

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
    baseline_subtracted: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable view."""
        return asdict(self)


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
        return {**asdict(self), "mean_energy_kwh": self.mean_energy_kwh}


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
    concurrency_sum: float = 0.0
    baseline_seen: bool = False


# --- attributor --------------------------------------------------------------


class EnergyAttributor:
    """Splits each sampling window's energy across the requests in flight.

    Args:
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
        subtract_baseline: bool = False,
        on_request: Callable[[RequestEnergy], None] | None = None,
        track_endpoints: bool = True,
    ) -> None:
        self.subtract_baseline = subtract_baseline
        self.on_request = on_request
        self.track_endpoints = track_endpoints

        self._in_flight: dict[int, _InFlight] = {}
        # begin/end run on the event-loop thread, on_window on the tracker's
        # scheduler thread. Never held across an on_request callback.
        self._lock = threading.Lock()
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
        with self._lock:
            self._in_flight[id(state)] = state
        return state

    def end(self, state: _InFlight) -> None:
        """Stamp the request finished.

        Deliberately does **not** settle. The request stays weighted until the
        next real sample closes, because at response time the machine's power
        over the last partial window is genuinely unknown - settling here would
        drop that energy into a zero-width window and silently lose it.
        """
        with self._lock:
            state.end = time.perf_counter()

    def close(self) -> None:
        """Emit every in-flight request as-is. Call after the tracker stops.

        Requests that never covered a window come out ``unresolved``.
        """
        with self._lock:
            pending = list(self._in_flight.values())
            self._in_flight.clear()
        for state in pending:
            self._emit(state)

    # -- window settlement ----------------------------------------------------

    def on_window(self, total_energy_kwh: float) -> None:
        """Close a sampling window with the tracker's cumulative energy.

        Wired to :meth:`~codecarbon.emissions_tracker.BaseEmissionsTracker.add_energy_window_observer`.
        Only ever called from a real hardware sample.
        """
        with self._lock:
            self._settle(total_energy_kwh)
            now = time.perf_counter()
            finished = [
                self._in_flight.pop(key)
                for key, state in list(self._in_flight.items())
                if state.end is not None and state.end <= now
            ]
        # Emitted outside the lock: on_request is user code and may call begin.
        for state in finished:
            self._emit(state)

    def _settle(self, total_energy_kwh: float) -> None:
        """Split one window. Caller must hold ``self._lock``."""
        now = time.perf_counter()
        w0, w1 = self._t_prev, now
        width = w1 - w0
        delta = total_energy_kwh - self._e_prev
        if width <= 0:
            self._t_prev, self._e_prev = now, total_energy_kwh
            return
        if delta < 0:
            # Counter wraparound or reset: no honest way to split a negative.
            self.windows_skipped += 1
            self._t_prev, self._e_prev = now, total_energy_kwh
            return

        states: list[_InFlight] = []
        weights: list[float] = []
        for state in self._in_flight.values():
            lo = max(state.start, w0)
            hi = min(state.end if state.end is not None else w1, w1)
            overlap = hi - lo
            if overlap <= 0:
                continue
            weights.append(overlap)
            state.overlap_s += overlap
            states.append(state)

        count = len(states)
        if count == 0:
            # Nothing in flight: this window is the machine idling.
            self._idle_power_w.append(delta * 3.6e6 / width)
            self.unattributed_kwh += delta
        else:
            total_weight = sum(weights)
            baseline_w = self.baseline_watts() if self.subtract_baseline else None
            # `is not None`, not truthiness: a measured 0.0 W idle baseline is
            # a baseline, and must still mark the results baseline_subtracted.
            base = (
                min(delta, baseline_w * width / 3.6e6)
                if baseline_w is not None
                else 0.0
            )
            dynamic = delta - base
            self.unattributed_kwh += base

            for state, weight in zip(states, weights):
                share = dynamic * (weight / total_weight)
                state.energy += share
                state.baseline_share += base / count
                state.baseline_seen = state.baseline_seen or baseline_w is not None
                state.windows += 1
                state.concurrency_sum += count
                self.attributed_kwh += share

        # Banked only once the split succeeded. The caller swallows exceptions,
        # so advancing the cursor first would drop this window's energy from
        # settled_kwh and break attributed + unattributed == settled.
        self.windows_settled += 1
        self.settled_kwh += delta
        self._t_prev, self._e_prev = now, total_energy_kwh

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
            "endpoints": {k: v.to_dict() for k, v in self.endpoints.items()},
            "attributed_kwh": self.attributed_kwh,
            "unattributed_kwh": self.unattributed_kwh,
            "total_kwh": self.attributed_kwh + self.unattributed_kwh,
            "settled_kwh": self.settled_kwh,
            "baseline_watts": self.baseline_watts(),
            "windows_settled": self.windows_settled,
            "windows_skipped": self.windows_skipped,
            "in_flight": len(self._in_flight),  # racy read, reporting only
        }
