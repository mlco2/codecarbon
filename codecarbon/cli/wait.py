"""CodeCarbon CLI - Wait Command"""

import re
import sys
import time
from datetime import datetime, timedelta, timezone

import typer
from rich import print

_DURATION_RE = re.compile(r"^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$")


def parse_duration(value: str) -> timedelta:
    """Parse "90m", "2h", "1h30m" or a plain number of seconds."""
    value = value.strip().lower()
    if value.isdigit():
        return timedelta(seconds=int(value))
    match = _DURATION_RE.match(value)
    if not match or not any(match.groups()):
        raise ValueError(f"Invalid duration: {value!r}. Use e.g. '90m', '2h', '1h30m'.")
    hours, minutes, seconds = (int(g or 0) for g in match.groups())
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


def find_green_window(
    duration: timedelta,
    deadline: timedelta,
    token: str | None,
):
    """Return (start, intensity, now_intensity) or None when we should run now.

    `now_intensity` is the first forecast point, i.e. the current period as the
    forecast sees it. Asking the /latest endpoint for a live value instead
    would be a second HTTP call for a number only used to print a percentage.
    """
    import pycountry

    from codecarbon.core.config import get_hierarchical_config
    from codecarbon.core.intensity_forecast import best_window, get_forecast
    from codecarbon.external.geography import GeoMetadata
    from codecarbon.input import DataSource

    # The tracker honours a configured country, so the forecast must too:
    # geolocating by IP would silently forecast the wrong grid.
    config = get_hierarchical_config()
    configured = config.get("country_iso_code")
    country = (
        pycountry.countries.get(alpha_3=configured.upper()) if configured else None
    )
    if country:
        geo = GeoMetadata(
            country_iso_code=country.alpha_3,
            country_name=country.name,
            region=config.get("region"),
            country_2letter_iso_code=country.alpha_2,
        )
    else:
        geo = GeoMetadata.from_geo_js(DataSource().geo_js_url)
    # A window may start as late as the deadline, so the forecast must cover
    # the deadline plus one job length.
    forecast = get_forecast(
        geo, token=token, horizon_hours=_ceil_hours(deadline + duration)
    )
    if forecast is None:
        return None

    now_intensity = forecast.points[0].g_co2e_per_kwh
    now = datetime.now(timezone.utc)
    start, intensity = best_window(forecast, duration, deadline=now + deadline)
    return start, intensity, now_intensity


def _ceil_hours(delta: timedelta) -> int:
    return max(1, -(-int(delta.total_seconds()) // 3600))


def wait_for_green_window(
    ctx: typer.Context,
    duration: str = "1h",
    deadline: str = "12h",
    finish_by: str | None = None,
    threshold: float | None = None,
    dry_run: bool = False,
    log_level: str = "error",
    **tracker_args,
):
    """Wait for the greenest window in the forecast, then run a command.

    This is a sleep, not a scheduler: it does not fork, daemonise or persist.
    For deferral that must survive a reboot, use cron, systemd or Airflow.

    Examples:

        # Print the recommendation and exit
        codecarbon wait --dry-run --deadline 24h --duration 90m

        # Block until the greenest window, then run under measurement
        codecarbon wait --deadline 12h --duration 2h -- python train.py

        # Bound the finish time instead of the start
        codecarbon wait --finish-by 8h --duration 2h -- python train.py
    """
    from codecarbon.cli.monitor import run_and_monitor
    from codecarbon.core.electricitymaps_api import resolve_token
    from codecarbon.external.logger import set_logger_level

    set_logger_level(log_level)

    try:
        job_duration = parse_duration(duration)
        # --deadline bounds the start, --finish-by bounds the end; the search
        # only ever needs the latest acceptable start.
        if finish_by is not None:
            max_delay = parse_duration(finish_by) - job_duration
            if max_delay < timedelta(0):
                raise ValueError(
                    f"--finish-by {finish_by} is sooner than --duration {duration}."
                )
        else:
            max_delay = parse_duration(deadline)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise typer.Exit(1)

    token = resolve_token()

    window = find_green_window(job_duration, max_delay, token)
    delay_seconds = 0.0
    if window is None:
        print("🌱 CodeCarbon: no forecast available, running now.")
    else:
        start, intensity, now_intensity = window
        delay_seconds = max(0.0, (start - datetime.now(timezone.utc)).total_seconds())
        if threshold is not None and now_intensity <= threshold:
            print(
                f"🌱 CodeCarbon: current intensity {now_intensity:.0f} gCO2e/kWh is "
                f"at or below the {threshold:.0f} threshold, running now."
            )
            delay_seconds = 0.0
        elif delay_seconds <= 0:
            print(
                f"🌱 CodeCarbon: now is already the greenest window "
                f"({now_intensity:.0f} gCO2e/kWh)."
            )
        else:
            saving = (
                100 * (now_intensity - intensity) / now_intensity
                if now_intensity
                else 0
            )
            print(
                f"🌱 Best start: {start:%Y-%m-%d %H:%M} UTC  "
                f"({intensity:.0f} gCO2e/kWh, now: {now_intensity:.0f})  "
                f"-> saves ~{saving:.0f}%"
            )

    if dry_run:
        raise typer.Exit(0)

    if delay_seconds > 0:
        print(
            f"   Waiting {delay_seconds / 3600:.1f}h before starting. "
            "Ctrl-C to abort."
        )
        try:
            time.sleep(delay_seconds)
        except KeyboardInterrupt:
            print("\n⚠️  Wait aborted, the command was not run.", file=sys.stderr)
            raise typer.Exit(130)

    run_and_monitor(ctx, log_level=log_level, **tracker_args)
