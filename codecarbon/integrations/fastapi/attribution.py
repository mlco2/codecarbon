"""Fair-share per-request energy attribution.

Each completed sampling window ``(t_prev, t_now, dE)`` is first split per
component into idle and dynamic energy::

    dynamic_c = max(dE_c - P_idle_c * width, 0)

Idle energy (and all RAM energy) goes to ``idle_kwh``: it would have been
drawn with no request at all, so charging it to whichever request happened to
be in flight is wrong. Of the dynamic CPU energy, only this process's share
of the machine's busy CPU time is kept; the rest goes to
``other_processes_kwh``. What is kept is split across the requests in flight
by the CPU time each one's meter saw in the window; what no meter claimed goes
to ``process_unattributed_kwh``. Dynamic GPU energy has no per-request signal
and is split by overlap with the window. Dynamic energy of windows with
nothing in flight goes to ``unattributed_kwh``. The invariant is::

    attributed_kwh + idle_kwh + other_processes_kwh
        + process_unattributed_kwh + unattributed_kwh == settled_kwh

exactly, after every window. That is the property the tests pin down.

Start/stop energy snapshots per request cannot do this: with N requests in
flight each one sees the whole machine's delta, so the sum overcounts by
roughly N (measured up to 88x at 100 concurrent requests).
"""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import psutil

from codecarbon.emissions_tracker import WindowSample
from codecarbon.external.logger import logger

#: Watt-seconds per kWh.
_WS_PER_KWH = 3.6e6
#: Weakest first: a request's quality is that of its weakest input.
_QUALITIES = ("none", "modeled", "measured")


@dataclass(frozen=True)
class RequestEnergy:
    """One request's finished attribution.

    ``energy_kwh`` and ``gpu_kwh`` are ``None`` when the request never covered
    a completed sampling window: there is no honest number, and zero would be
    a lie.
    """

    endpoint: str
    #: CPU energy above idle, charged by the CPU time the request used.
    energy_kwh: float | None
    #: GPU energy above idle, charged by wall-clock overlap with the window.
    gpu_kwh: float | None
    duration_s: float
    #: Completed sampling windows this request was in flight for.
    windows: int
    #: Mean number of requests in flight with it, per window.
    mean_concurrency: float | None
    #: CPU time the meter saw this request use, in seconds.
    cpu_seconds: float
    #: ``"cpu_time"``, ``"wall"`` (GPU energy only) or ``"mixed"`` (both).
    attribution_method: str
    #: ``"measured"`` (RAPL, powermetrics, NVML...), ``"modeled"`` (CPU load
    #: mode) or ``"none"`` (constant TDP, or no window), for the weakest
    #: component the request was charged from.
    quality: str


def _thread_clock() -> int | None:
    """The calling thread's CPU clock, readable from other threads (Linux)."""
    if not hasattr(time, "pthread_getcpuclockid"):
        return None
    try:
        return time.pthread_getcpuclockid(threading.get_ident())
    except OSError:
        return None


class _Meter:
    """CPU time used by one request, in ns.

    ``ns`` is the event-loop time. It is written only by the loop thread
    driving the request, so it needs no lock, with or without the GIL.
    Worker-thread calls (:meth:`run_in_thread`) go through ``_lock``. While
    one runs, :meth:`total_ns` reads its CPU clock from the outside where the
    platform allows it (Linux), so a long sync call is charged window by
    window. Elsewhere its CPU time only shows up once it returns.
    """

    __slots__ = ("ns", "_lock", "_thread_ns", "_running")

    def __init__(self) -> None:
        self.ns = 0
        self._lock = threading.Lock()
        self._thread_ns = 0
        #: Worker thread id -> (its CPU clock or None, thread time at start).
        self._running: dict[int, tuple[int | None, int]] = {}

    def run_in_thread(self, func: Callable[..., Any], *args: Any) -> Any:
        """Call ``func(*args)`` on this worker thread, adding its CPU time."""
        ident = threading.get_ident()
        clock = _thread_clock()
        start = time.thread_time_ns()
        with self._lock:
            self._running[ident] = (clock, start)
        try:
            return func(*args)
        finally:
            used = time.thread_time_ns() - start
            with self._lock:
                del self._running[ident]
                self._thread_ns += used

    def total_ns(self) -> int:
        """CPU time so far, including worker calls still running."""
        with self._lock:
            total = self.ns + self._thread_ns
            for clock, start in self._running.values():
                if clock is not None:
                    try:
                        total += max(time.clock_gettime_ns(clock) - start, 0)
                    except OSError:
                        pass
        return total


class _Metered:
    """Awaitable that drives ``coro`` and meters it.

    Adds ``time.thread_time_ns()`` spent inside each ``send``/``throw`` of the
    coroutine to ``meter``. Work the coroutine hands to other threads or to
    child tasks is not seen.
    """

    __slots__ = ("_coro", "_meter")

    def __init__(self, coro: Any, meter: _Meter) -> None:
        self._coro = coro
        self._meter = meter

    def __await__(self):
        coro, meter, clock = self._coro, self._meter, time.thread_time_ns
        value: Any = None
        error: BaseException | None = None
        while True:
            start = clock()
            try:
                if error is None:
                    yielded = coro.send(value)
                else:
                    yielded = coro.throw(error)
            except StopIteration as stop:
                meter.ns += clock() - start
                return stop.value
            except BaseException:
                meter.ns += clock() - start
                raise
            meter.ns += clock() - start
            value = error = None
            try:
                value = yield yielded
            except GeneratorExit:
                start = clock()
                try:
                    coro.close()
                finally:
                    meter.ns += clock() - start
                raise
            except BaseException as exc:
                error = exc


@dataclass
class _InFlight:
    """Mutable per-request state, freed as soon as the request emits."""

    endpoint: str
    start: float
    meter: _Meter | None = None
    #: ``meter.total_ns()`` already charged in earlier windows.
    cpu_seen_ns: int = 0
    end: float | None = None
    energy: float = 0.0
    gpu_energy: float = 0.0
    quality: str | None = None
    windows: int = 0
    concurrency_sum: float = 0.0
    #: Called with the :class:`RequestEnergy` when this request resolves.
    on_resolved: Callable[[RequestEnergy], None] | None = None


def _cpu_times() -> tuple[float, float, float]:
    """``(process CPU s, machine busy CPU s, machine total CPU s)``, cumulative.

    Busy excludes idle, iowait and steal (time the hypervisor gave to another
    guest). ``guest`` and ``guest_nice`` are already counted in ``user`` and
    ``nice`` on Linux, so they are taken out of the total, as psutil does.
    """
    t = psutil.cpu_times()
    total = sum(t) - getattr(t, "guest", 0.0) - getattr(t, "guest_nice", 0.0)
    busy = total - t.idle - getattr(t, "iowait", 0.0) - getattr(t, "steal", 0.0)
    return time.process_time(), busy, total


class _IdleEstimator:
    """Idle power of one component, in W.

    The lower of the rolling minimum of window power over ``horizon_s`` and,
    once 20 windows with a utilisation are known and the fit is good
    (R² > 0.8), the intercept of ``power = a + b * utilisation``. The minimum
    alone overestimates idle on a server that is never idle; the intercept
    alone is noise when load barely varies.
    """

    def __init__(self, horizon_s: float) -> None:
        self._horizon_s = horizon_s
        # (t, power) with increasing power: the front is the window minimum.
        self._mins: deque[tuple[float, float]] = deque()
        self._points: deque[tuple[float, float, float]] = deque()
        #: Latest estimate, ``None`` before the first window.
        self.watts: float | None = None

    def update(self, t: float, power: float, util: float | None = None) -> float:
        cutoff = t - self._horizon_s
        while self._mins and self._mins[0][0] < cutoff:
            self._mins.popleft()
        while self._mins and self._mins[-1][1] >= power:
            self._mins.pop()
        self._mins.append((t, power))
        estimate = self._mins[0][1]
        if util is not None:
            self._points.append((t, util, power))
            while self._points[0][0] < cutoff:
                self._points.popleft()
            intercept = _intercept(self._points)
            if intercept is not None:
                estimate = min(estimate, intercept)
        self.watts = estimate
        return estimate


def _intercept(points: deque[tuple[float, float, float]]) -> float | None:
    """Least-squares intercept of power on utilisation, ``None`` if unreliable."""
    # ponytail: full O(n) refit per window, n = horizon / measure_power_secs
    # (3600 at 1 s, about 1 ms). Keep running sums if that ever shows up.
    n = len(points)
    if n < 20:
        return None
    mean_u = sum(u for _, u, _ in points) / n
    mean_p = sum(p for _, _, p in points) / n
    sxx = sum((u - mean_u) ** 2 for _, u, _ in points)
    syy = sum((p - mean_p) ** 2 for _, _, p in points)
    if sxx <= 0 or syy <= 0:
        return None
    sxy = sum((u - mean_u) * (p - mean_p) for _, u, p in points)
    if sxy * sxy / (sxx * syy) <= 0.8:
        return None
    return max(mean_p - sxy / sxx * mean_u, 0.0)


def _dynamic(delta_kwh: float, idle_w: float, width: float) -> float:
    """Energy above idle in one window, within ``[0, delta_kwh]``."""
    return min(max(delta_kwh - idle_w * width / _WS_PER_KWH, 0.0), delta_kwh)


class EnergyAttributor:
    """Splits each sampling window's dynamic energy across the requests in flight.

    Args:
        clock: Must be the clock of :attr:`WindowSample.timestamp`.
        cpu_times: Returns cumulative ``(process, busy, total)`` CPU seconds;
            replaceable for tests.
        idle_horizon_s: How far back the idle-power estimate looks.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.perf_counter,
        cpu_times: Callable[[], tuple[float, float, float]] = _cpu_times,
        idle_horizon_s: float = 3600.0,
    ) -> None:
        self._clock = clock
        self._cpu_times = cpu_times
        self._in_flight: dict[int, _InFlight] = {}
        # begin/end run on the event-loop thread, on_window on the tracker's
        # scheduler thread. Never held across an on_resolved callback.
        self._lock = threading.Lock()
        #: Running sum of everything handed to requests, kWh.
        self.attributed_kwh = 0.0
        #: Energy the machine would have drawn with no load (idle power, and
        #: all of RAM), kWh.
        self.idle_kwh = 0.0
        #: Dynamic CPU energy of the machine's other processes, kWh.
        self.other_processes_kwh = 0.0
        #: Our CPU dynamic energy that no request's meter claimed: work in
        #: threads, child tasks, the server itself, kWh.
        self.process_unattributed_kwh = 0.0
        #: Dynamic energy from windows with nothing in flight, kWh.
        self.unattributed_kwh = 0.0
        #: Energy taken in from closed windows. The buckets add up to it
        #: exactly after every window; it is below the tracker's run total by
        #: whatever a wrapped counter dropped (``windows_skipped``) plus the
        #: final unsampled partial window.
        self.settled_kwh = 0.0
        self.windows_settled = 0
        #: Windows where an energy counter went backwards (RAPL wrap/reset).
        self.windows_skipped = 0
        self._cpu_idle = _IdleEstimator(idle_horizon_s)
        self._gpu_idle = _IdleEstimator(idle_horizon_s)
        self._prev: WindowSample | None = None
        self._t_prev = clock()
        self._times_prev = (0.0, 0.0, 0.0)

    def reset_window(self, sample: WindowSample) -> None:
        """Anchor the first window at ``sample``. Call when the tracker starts."""
        with self._lock:
            self._prev = sample
            self._t_prev = sample.timestamp
            self._times_prev = self._cpu_times()

    def begin(self, endpoint: str, meter: _Meter | None = None) -> _InFlight:
        """Start weighting a request. Returns the handle to pass to :meth:`end`.

        ``meter`` is the request's CPU meter; without one it gets no CPU energy.
        """
        state = _InFlight(endpoint=endpoint, start=self._clock(), meter=meter)
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
            state.end = self._clock()

    def close(self) -> None:
        """Emit every in-flight request as-is. Call after the tracker stops."""
        with self._lock:
            pending = list(self._in_flight.values())
            self._in_flight.clear()
        for state in pending:
            self._emit(state)

    def on_window(self, sample: WindowSample) -> None:
        """Close a sampling window with the tracker's cumulative energies.

        Wired to
        :meth:`~codecarbon.emissions_tracker.BaseEmissionsTracker.add_energy_window_observer`,
        so it is only ever called from a real hardware sample.
        """
        with self._lock:
            self._settle(sample)
            finished = [
                self._in_flight.pop(key)
                for key, state in list(self._in_flight.items())
                if state.end is not None
            ]
        # Emitted outside the lock: on_resolved is user code and may call begin.
        for state in finished:
            self._emit(state)

    def _settle(self, sample: WindowSample) -> None:
        """Split one window. Caller must hold ``self._lock``."""
        prev, w0, times_prev = self._prev, self._t_prev, self._times_prev
        times = self._cpu_times()
        w1 = sample.timestamp
        width = w1 - w0
        if prev is None or width <= 0:
            self._prev, self._t_prev, self._times_prev = sample, w1, times
            return
        delta = sample.total_kwh - prev.total_kwh
        d_cpu = sample.cpu_kwh - prev.cpu_kwh
        d_gpu = sample.gpu_kwh - prev.gpu_kwh
        if min(delta, d_cpu, d_gpu) < 0:
            # Counter wraparound or reset: no honest way to split a negative.
            # The CPU time metered in it is dropped with it, or the next
            # window would charge it against a process time that excludes it.
            self.windows_skipped += 1
            for state in self._in_flight.values():
                state.cpu_seen_ns = state.meter.total_ns() if state.meter else 0
            self._prev, self._t_prev, self._times_prev = sample, w1, times
            return

        d_proc, d_busy, d_total = (now - then for now, then in zip(times, times_prev))
        util = d_busy / d_total if d_total > 0 else None
        cpu_idle_w = sample.cpu_idle_w
        if cpu_idle_w is None:
            cpu_idle_w = self._cpu_idle.update(w1, d_cpu * _WS_PER_KWH / width, util)
        else:
            self._cpu_idle.watts = cpu_idle_w
        dynamic_cpu = _dynamic(d_cpu, cpu_idle_w, width)
        # This process's share of the machine's busy CPU time. psutil counts in
        # clock ticks (10 ms on Linux), so short windows are noisy: clamped.
        if sample.cpu_per_process:
            share = 1.0  # load mode in process tracking: already ours alone
        elif d_busy > 0:
            share = min(max(d_proc / d_busy, 0.0), 1.0)
        else:
            share = 1.0 if d_proc > 0 else 0.0
        ours = dynamic_cpu * share
        other = dynamic_cpu - ours
        dynamic_gpu = 0.0
        if sample.gpu_quality is not None:
            gpu_idle_w = self._gpu_idle.update(w1, d_gpu * _WS_PER_KWH / width)
            dynamic_gpu = _dynamic(d_gpu, gpu_idle_w, width)

        quality = sample.cpu_quality
        if sample.gpu_quality is not None:
            quality = min(quality, sample.gpu_quality, key=_QUALITIES.index)

        states = list(self._in_flight.values())
        # CPU: each request gets our share in proportion to the CPU time its
        # meter saw this window. If the meters claim more than the process
        # used (clock granularity), they are scaled down to fit.
        seen = [state.meter.total_ns() if state.meter else 0 for state in states]
        used = [now - state.cpu_seen_ns for now, state in zip(seen, states)]
        denominator = max(sum(used), max(d_proc, 0.0) * 1e9)
        cpu_parts = [ours * ns / denominator if denominator > 0 else 0.0 for ns in used]
        # GPU: no per-request signal, so split by overlap with the window.
        weights = []
        for state in states:
            lo = max(state.start, w0)
            hi = min(state.end if state.end is not None else w1, w1)
            weights.append(max(hi - lo, 0.0))
        total_weight = sum(weights)
        gpu_parts = [
            dynamic_gpu * weight / total_weight if total_weight > 0 else 0.0
            for weight in weights
        ]

        if not states:
            self.unattributed_kwh += ours + dynamic_gpu
        else:
            cpu_attributed, gpu_attributed = sum(cpu_parts), sum(gpu_parts)
            for state, now, cpu_part, gpu_part in zip(
                states, seen, cpu_parts, gpu_parts
            ):
                state.cpu_seen_ns = now
                state.energy += cpu_part
                state.gpu_energy += gpu_part
                state.quality = min(
                    quality, state.quality or quality, key=_QUALITIES.index
                )
                state.windows += 1
                state.concurrency_sum += len(states)
            self.attributed_kwh += cpu_attributed + gpu_attributed
            self.process_unattributed_kwh += ours - cpu_attributed
            # No overlap at all (or rounding): nobody to give it to.
            self.unattributed_kwh += dynamic_gpu - gpu_attributed
        self.other_processes_kwh += other
        self.idle_kwh += delta - dynamic_cpu - dynamic_gpu
        # Banked only once the split succeeded. The caller swallows exceptions,
        # so advancing the cursor first would drop this window's energy from
        # settled_kwh; left in place, the next window covers it.
        self.windows_settled += 1
        self.settled_kwh += delta
        self._prev, self._t_prev, self._times_prev = sample, w1, times

    def _emit(self, state: _InFlight) -> None:
        if state.energy > 0 and state.gpu_energy > 0:
            method = "mixed"
        elif state.gpu_energy > 0:
            method = "wall"
        else:
            method = "cpu_time"
        result = RequestEnergy(
            endpoint=state.endpoint,
            energy_kwh=state.energy if state.windows else None,
            gpu_kwh=state.gpu_energy if state.windows else None,
            duration_s=(state.end or self._clock()) - state.start,
            windows=state.windows,
            mean_concurrency=(
                state.concurrency_sum / state.windows if state.windows else None
            ),
            cpu_seconds=state.meter.total_ns() / 1e9 if state.meter else 0.0,
            attribution_method=method,
            quality=state.quality or "none",
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
            "idle_kwh": self.idle_kwh,
            "other_processes_kwh": self.other_processes_kwh,
            "process_unattributed_kwh": self.process_unattributed_kwh,
            "unattributed_kwh": self.unattributed_kwh,
            "settled_kwh": self.settled_kwh,
            "idle_power_w": {"cpu": self._cpu_idle.watts, "gpu": self._gpu_idle.watts},
            "quality": {
                "cpu": self._prev.cpu_quality if self._prev else None,
                "gpu": self._prev.gpu_quality if self._prev else None,
            },
            "windows_settled": self.windows_settled,
            "windows_skipped": self.windows_skipped,
            "in_flight": len(self._in_flight),  # racy read, reporting only
        }
