"""Carbon intensity forecasts and greenest-window selection.

The only provider able to serve a forecast today is Electricity Maps, and only
for users holding a token for it. When no provider can answer, `get_forecast`
returns ``None`` and every caller must degrade to "run now" -- a job is never
blocked on a missing credential.

HTTP goes through `codecarbon.core.electricitymaps_api.request`, so a failing
API backs off once for the whole process instead of once per caller. The
forecast response itself is not cached: it is fetched once per `codecarbon
wait` invocation, and its useful lifetime is nothing like the current
intensity's short TTL.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from codecarbon.core.electricitymaps_api import FORECAST_URL, location_params, request
from codecarbon.external.geography import GeoMetadata
from codecarbon.external.logger import logger


@dataclass(frozen=True)
class IntensityPoint:
    at: datetime  # timezone-aware, UTC
    g_co2e_per_kwh: float


@dataclass(frozen=True)
class Forecast:
    zone: str
    points: List[IntensityPoint]  # ordered, typically hourly


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def get_forecast(
    geo: GeoMetadata,
    *,
    token: Optional[str] = None,
    horizon_hours: int = 48,
) -> Optional[Forecast]:
    """Return an intensity forecast, or None when no provider can supply one.

    Never raises: a forecast is an optimisation, not a requirement.
    """
    if not token:
        logger.warning(
            "No Electricity Maps API token configured, cannot fetch a carbon "
            "intensity forecast."
        )
        return None

    try:
        data = request(FORECAST_URL, location_params(geo), token)
        horizon_end = datetime.now(timezone.utc) + timedelta(hours=horizon_hours)
        points = [
            IntensityPoint(
                at=_parse_datetime(entry["datetime"]),
                g_co2e_per_kwh=float(entry["carbonIntensity"]),
            )
            for entry in data["forecast"]
            if entry.get("carbonIntensity") is not None
        ]
        points = sorted(
            (point for point in points if point.at <= horizon_end),
            key=lambda point: point.at,
        )
        if not points:
            raise ValueError("No usable forecast points in response")

        return Forecast(
            zone=data.get("zone", ""),
            points=points,
        )
    except Exception as e:
        logger.error(
            f"intensity_forecast.get_forecast: {type(e).__name__}: {e} "
            ">>> Falling back to running now."
        )
        return None


def best_window(
    forecast: Forecast,
    duration: timedelta,
    deadline: Optional[datetime] = None,
) -> Tuple[datetime, float]:
    """Start time minimising mean intensity over `duration`, and that mean.

    `deadline` is the latest acceptable *start* time -- the job may run past
    it. Only windows starting at or after the first forecast point, at or
    before `deadline`, and fully covered by the forecast are considered.
    Returns the earliest point and its intensity when no complete window fits,
    so "just run it" is the default.
    """
    points = forecast.points
    fallback = (points[0].at, points[0].g_co2e_per_kwh)

    # The forecast covers up to one step past its last point. Gaps are not
    # guaranteed uniform, so the smallest one is the safe assumption.
    step = (
        min(b.at - a.at for a, b in zip(points, points[1:]))
        if len(points) > 1
        else duration
    )
    covered_until = points[-1].at + step

    best: Optional[Tuple[datetime, float]] = None
    for start_index, start in enumerate(points):
        window_end = start.at + duration
        if window_end > covered_until:
            break
        if deadline is not None and start.at > deadline:
            break
        # ponytail: linear rescan per start, fine for hourly points over a few
        # days; use a running sum if horizons ever grow by orders of magnitude.
        # Each point holds until the next one, so weight it by how much of its
        # period falls inside the window: an hourly point half-covered by the
        # window's end must not count as a full hour.
        covered = [point for point in points[start_index:] if point.at < window_end]
        ends = [point.at for point in covered[1:]] + [window_end]
        weights = [
            (min(end, window_end) - point.at).total_seconds()
            for point, end in zip(covered, ends)
        ]
        mean = sum(
            point.g_co2e_per_kwh * weight for point, weight in zip(covered, weights)
        ) / sum(weights)
        if best is None or mean < best[1]:
            best = (start.at, mean)

    return best or fallback
