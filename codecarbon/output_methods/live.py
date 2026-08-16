"""Live terminal view of the current run, used by `codecarbon monitor --live`."""

from rich.console import Console
from rich.live import Live
from rich.table import Table

from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData


def _table(data: EmissionsData) -> Table:
    table = Table(title="CodeCarbon live")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for name, value in (
        ("Duration", f"{data.duration:,.0f} s"),
        ("Emissions", f"{data.emissions * 1000:,.3f} gCO2eq"),
        ("Energy", f"{data.energy_consumed * 1000:,.3f} Wh"),
        ("CPU power", f"{data.cpu_power:,.1f} W"),
        ("GPU power", f"{data.gpu_power:,.1f} W"),
        ("RAM power", f"{data.ram_power:,.1f} W"),
    ):
        table.add_row(name, value)
    return table


class LiveTableOutput(BaseOutput):
    """Reprint a Rich table in the terminal on every measure."""

    live_out_every_measure = True

    def __init__(self, console: Console | None = None):
        self._live = Live(console=console, refresh_per_second=4)
        self._live.start()

    def live_out(self, total: EmissionsData, delta: EmissionsData | None = None):
        self._live.update(_table(total))

    def exit(self):
        self._live.stop()
