"""Fair-share per-request energy attribution.

Each completed sampling window ``(t_prev, t_now, dE)`` is split across the
requests that were in flight during it, weighted by their overlap with the
window and normalised **by the sum of the weights**. Windows with nothing in
flight go entirely to ``unattributed_kwh``. The invariant is::

    attributed_kwh + unattributed_kwh == settled_kwh

exactly, after every window. That is the property the tests pin down.

Start/stop energy snapshots per request cannot do this: with N requests in
flight each one sees the whole machine's delta, so the sum overcounts by
roughly N (measured up to 88x at 100 concurrent requests).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from codecarbon.external.logger import logger


@dataclass(frozen=True)
class RequestEnergy:
    """One request's finished attribution.

    ``energy_kwh`` is ``None`` when the request never covered a completed
    sampling window: there is no honest number, and zero would be a lie.
    """

    endpoint: str
    energy_kwh: float | None
    duration_s: float
    #: Completed sampling windows this request overlapped.
    windows: int
    #: Mean number of requests it competed against, window-weighted.
    mean_concurrency: float | None


@dataclass
class _InFlight:
    """Mutable per-request state, freed as soon as the request emits."""

    endpoint: str
    start: float
    end: float | None = None
    energy: float = 0.0
    windows: int = 0
    concurrency_sum: float = 0.0
    #: Called with the :class:`RequestEnergy` when this request resolves.
    on_resolved: Callable[[RequestEnergy], None] | None = None


class EnergyAttributor:
    """Splits each sampling window's energy across the requests in flight."""

    def __init__(self) -> None:
        self._in_flight: dict[int, _InFlight] = {}
        # begin/end run on the event-loop thread, on_window on the tracker's
        # scheduler thread. Never held across an on_resolved callback.
        self._lock = threading.Lock()
        #: Running sum of everything handed to requests, kWh.
        self.attributed_kwh = 0.0
        #: Energy from windows with nothing in flight, kWh.
        self.unattributed_kwh = 0.0
        #: Energy taken in from closed windows. ``attributed + unattributed ==
        #: settled`` holds exactly after every window; it is below the tracker's
        #: run total by whatever a wrapped counter dropped
        #: (``windows_skipped``) plus the final unsampled partial window.
        self.settled_kwh = 0.0
        self.windows_settled = 0
        #: Windows where the energy counter went backwards (RAPL wrap/reset).
        self.windows_skipped = 0
        self._t_prev = time.perf_counter()
        self._e_prev = 0.0

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
        """Emit every in-flight request as-is. Call after the tracker stops."""
        with self._lock:
            pending = list(self._in_flight.values())
            self._in_flight.clear()
        for state in pending:
            self._emit(state)

    def on_window(self, total_energy_kwh: float) -> None:
        """Close a sampling window with the tracker's cumulative energy.

        Wired to
        :meth:`~codecarbon.emissions_tracker.BaseEmissionsTracker.add_energy_window_observer`,
        so it is only ever called from a real hardware sample.
        """
        with self._lock:
            self._settle(total_energy_kwh)
            finished = [
                self._in_flight.pop(key)
                for key, state in list(self._in_flight.items())
                if state.end is not None
            ]
        # Emitted outside the lock: on_resolved is user code and may call begin.
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
            if hi - lo <= 0:
                continue
            weights.append(hi - lo)
            states.append(state)

        if not states:
            self.unattributed_kwh += delta
        else:
            total_weight = sum(weights)
            for state, weight in zip(states, weights):
                share = delta * (weight / total_weight)
                state.energy += share
                state.windows += 1
                state.concurrency_sum += len(states)
                self.attributed_kwh += share

        # Banked only once the split succeeded. The caller swallows exceptions,
        # so advancing the cursor first would drop this window's energy from
        # settled_kwh and break attributed + unattributed == settled.
        self.windows_settled += 1
        self.settled_kwh += delta
        self._t_prev, self._e_prev = now, total_energy_kwh

    def _emit(self, state: _InFlight) -> None:
        result = RequestEnergy(
            endpoint=state.endpoint,
            energy_kwh=state.energy if state.windows else None,
            duration_s=(state.end or time.perf_counter()) - state.start,
            windows=state.windows,
            mean_concurrency=(
                state.concurrency_sum / state.windows if state.windows else None
            ),
        )
        if state.on_resolved is not None:
            try:
                state.on_resolved(result)
            except Exception:
                logger.exception("CodeCarbon attribution callback failed")

    def report(self) -> dict[str, Any]:
        """Run-level accounting, for checking what the split did."""
        return {
            "attributed_kwh": self.attributed_kwh,
            "unattributed_kwh": self.unattributed_kwh,
            "settled_kwh": self.settled_kwh,
            "windows_settled": self.windows_settled,
            "windows_skipped": self.windows_skipped,
            "in_flight": len(self._in_flight),  # racy read, reporting only
        }
