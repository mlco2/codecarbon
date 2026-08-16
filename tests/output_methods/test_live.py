import dataclasses
import io

from rich.console import Console

from codecarbon.output_methods.emissions_data import EmissionsData
from codecarbon.output_methods.live import LiveTableOutput, _table


def _emissions_data(**overrides) -> EmissionsData:
    """An EmissionsData with 0 everywhere but the fields the live table shows."""
    kwargs = {
        field.name: 0
        for field in dataclasses.fields(EmissionsData)
        if field.default is dataclasses.MISSING
        and field.default_factory is dataclasses.MISSING
    }
    kwargs.update(
        duration=3661.4,
        emissions=0.001234,
        energy_consumed=0.0025,
        cpu_power=12.34,
        gpu_power=56.78,
        ram_power=9.87,
    )
    kwargs.update(overrides)
    return EmissionsData(**kwargs)


def _render(renderable) -> str:
    console = Console(file=io.StringIO(), force_terminal=False, width=120, record=True)
    console.print(renderable)
    return console.export_text()


def test_table_renders_every_metric_row_formatted():
    text = _render(_table(_emissions_data()))

    assert "CodeCarbon live" in text
    assert "3,661 s" in text  # duration, no decimals
    assert "1.234 gCO2eq" in text  # emissions, kg -> g
    assert "2.500 Wh" in text  # energy, kWh -> Wh
    assert "12.3 W" in text
    assert "56.8 W" in text
    assert "9.9 W" in text


def test_live_output_starts_updates_and_stops():
    console = Console(file=io.StringIO(), force_terminal=False, width=120)
    out = LiveTableOutput(console=console)
    try:
        assert out.live_out_every_measure is True
        assert out._live.is_started
        out.live_out(_emissions_data())
        out.live_out(_emissions_data(duration=42), delta=_emissions_data())
    finally:
        out.exit()

    assert not out._live.is_started


def test_exit_is_safe_when_called_twice():
    out = LiveTableOutput(
        console=Console(file=io.StringIO(), force_terminal=False, width=120)
    )
    out.exit()
    out.exit()

    assert not out._live.is_started
