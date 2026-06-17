"""
Lightweight entry point for ``codecarbon monitor``.

Avoids importing auth, questionary, and API client modules required by other CLI
commands — roughly 500 ms faster cold start than ``codecarbon.cli.main``.
"""

import typer
from typing_extensions import Annotated

from codecarbon.cli.monitor import run_and_monitor

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)


@app.command("monitor")
def monitor(
    ctx: typer.Context,
    measure_power_secs: Annotated[
        int,
        typer.Option(help="Interval between two measures."),
    ] = 10,
    api_call_interval: Annotated[
        int,
        typer.Option(help="Number of measures between API calls."),
    ] = 30,
    api: Annotated[
        bool,
        typer.Option(help="Choose to call Code Carbon API or not"),
    ] = True,
    offline: Annotated[bool, typer.Option(help="Run in offline mode")] = False,
    country_iso_code: Annotated[
        str,
        typer.Option(help="3-letter country ISO code for offline mode"),
    ] = None,
    region: Annotated[
        str,
        typer.Option(help="Region/province for offline mode"),
    ] = None,
    log_level: Annotated[
        str,
        typer.Option(help="Log level (critical, error, warning, info, debug)"),
    ] = "error",
):
    """Monitor a command's emissions with minimal CLI import overhead."""
    tracker_args = {
        "measure_power_secs": measure_power_secs,
        "api_call_interval": api_call_interval,
        "log_level": log_level,
    }
    if offline:
        if not country_iso_code:
            typer.echo(
                "ERROR: Country ISO code is required for offline mode "
                "(e.g. --country-iso-code FRA).",
                err=True,
            )
            raise typer.Exit(1)
        tracker_args.update({"country_iso_code": country_iso_code, "region": region})
    else:
        from codecarbon.cli.cli_utils import get_existing_exp_id

        experiment_id = get_existing_exp_id()
        if api and experiment_id is None:
            typer.echo(
                "ERROR: No experiment id. Use --offline --country-iso-code FRA "
                "or configure an experiment first.",
                err=True,
            )
            raise typer.Exit(1)
        tracker_args["save_to_api"] = api

    if getattr(ctx, "args", None):
        return run_and_monitor(ctx, offline=offline, **tracker_args)

    typer.echo("Use: codecarbon-monitor monitor -- <command>")
    raise typer.Exit(1)


def main() -> None:
    app(prog_name="codecarbon-monitor")


if __name__ == "__main__":
    main()
