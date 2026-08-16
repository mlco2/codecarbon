"""Tests for the measurement quality diagnostics and the `codecarbon detect` CLI."""

import json
import os
from types import SimpleNamespace

from typer.testing import CliRunner

from codecarbon import diagnostics
from codecarbon.cli import main as cli_main
from codecarbon.diagnostics import (
    ESTIMATED,
    MEASURED,
    UNAVAILABLE,
    ComponentDiagnostic,
    diagnose,
    render_text,
    summary,
)
from codecarbon.external import hardware, ram

# diagnose() dispatches with isinstance, so the fixtures must be real hardware
# instances. Their __init__ probes the machine, so build them bare and set only
# the attributes the diagnostics read.


def _bare(cls, **attributes):
    instance = object.__new__(cls)
    instance.__dict__.update(attributes)
    return instance


def CPU(mode, model="Fake CPU", tdp=65, is_generic_tdp=False):
    return _bare(
        hardware.CPU,
        _mode=mode,
        _model=model,
        _tdp=tdp,
        _is_generic_tdp=is_generic_tdp,
    )


def AppleSiliconChip(chip_part="CPU", model="Apple M2"):
    return _bare(hardware.AppleSiliconChip, chip_part=chip_part, _model=model)


def RAM(force_ram_power=None):
    return _bare(ram.RAM, _force_ram_power=force_ram_power, machine_memory_GB=32.0)


def GPU(names, power_usage=42159):
    details = [{"name": name, "power_usage": power_usage} for name in names]
    return _bare(
        hardware.GPU,
        devices=SimpleNamespace(
            device_count=len(details), get_gpu_details=lambda: details
        ),
    )


def _make_rapl_tree(tmp_path, readable):
    root = tmp_path / "intel-rapl"
    domain = root / "intel-rapl:0"
    domain.mkdir(parents=True)
    energy = domain / "energy_uj"
    energy.write_text("1000")
    energy.chmod(0o444 if readable else 0o000)
    return root


def test_cpu_measured_with_rapl():
    (found,) = [d for d in diagnose([CPU("intel_rapl")]) if d.component == "CPU"]
    assert found.status == MEASURED
    assert found.method == "RAPL"
    assert found.reason is None


def test_cpu_estimated_when_rapl_unreadable(tmp_path, monkeypatch):
    root = _make_rapl_tree(tmp_path, readable=False)
    monkeypatch.setattr(diagnostics, "DEFAULT_RAPL_ROOT", str(root))
    monkeypatch.setattr(diagnostics, "is_linux_os", lambda: True)
    monkeypatch.setattr(diagnostics, "is_mac_os", lambda: False)

    (found,) = [d for d in diagnose([CPU("cpu_load")]) if d.component == "CPU"]
    assert found.status == ESTIMATED
    if os.geteuid() != 0:  # root can read anything, the distinction is moot
        assert "permission denied" in found.reason
        assert "chmod" in found.fix


def test_no_powercap_reason_differs_from_unreadable(tmp_path, monkeypatch):
    monkeypatch.setattr(diagnostics, "is_linux_os", lambda: True)
    monkeypatch.setattr(diagnostics, "is_mac_os", lambda: False)

    monkeypatch.setattr(diagnostics, "DEFAULT_RAPL_ROOT", str(tmp_path / "absent"))
    absent = diagnose([CPU("cpu_load")])[0].reason

    root = _make_rapl_tree(tmp_path, readable=False)
    monkeypatch.setattr(diagnostics, "DEFAULT_RAPL_ROOT", str(root))
    unreadable = diagnose([CPU("cpu_load")])[0].reason

    assert absent != unreadable
    assert "not an Intel/AMD RAPL platform" in absent


def _force_platform(monkeypatch, linux=False, mac=False, windows=False):
    monkeypatch.setattr(diagnostics, "is_linux_os", lambda: linux)
    monkeypatch.setattr(diagnostics, "is_mac_os", lambda: mac)
    monkeypatch.setattr(diagnostics, "is_windows_os", lambda: windows)


def test_readable_rapl_not_selected_is_reported(tmp_path, monkeypatch):
    root = _make_rapl_tree(tmp_path, readable=True)
    monkeypatch.setattr(diagnostics, "DEFAULT_RAPL_ROOT", str(root))
    _force_platform(monkeypatch, linux=True)

    (found,) = [d for d in diagnose([CPU("cpu_load")]) if d.component == "CPU"]
    assert found.status == ESTIMATED
    assert "readable but was not selected" in found.reason
    # a readable tree must not be reported as a permission problem
    assert "permission denied" not in found.reason
    assert "chmod" in found.fix


def test_rapl_root_without_energy_counter(tmp_path, monkeypatch):
    root = tmp_path / "intel-rapl"
    root.mkdir()
    monkeypatch.setattr(diagnostics, "DEFAULT_RAPL_ROOT", str(root))
    _force_platform(monkeypatch, linux=True)

    (found,) = [d for d in diagnose([CPU("cpu_load")]) if d.component == "CPU"]
    assert "exposes no energy counter" in found.reason


def test_macos_powermetrics_available_but_unused(monkeypatch):
    _force_platform(monkeypatch, mac=True)
    monkeypatch.setattr(
        diagnostics.powermetrics, "is_powermetrics_available", lambda: True
    )

    (found,) = [d for d in diagnose([CPU("cpu_load")]) if d.component == "CPU"]
    assert found.reason == "powermetrics is available but was not selected"
    assert "passwordless sudo" in found.fix


def test_macos_powermetrics_missing_asks_for_sudo_rule(monkeypatch):
    _force_platform(monkeypatch, mac=True)
    monkeypatch.setattr(
        diagnostics.powermetrics, "is_powermetrics_available", lambda: False
    )

    (found,) = [d for d in diagnose([CPU("cpu_load")]) if d.component == "CPU"]
    assert "passwordless sudo rule" in found.reason


def test_windows_emi_reasons_and_no_fix(monkeypatch):
    _force_platform(monkeypatch, windows=True)

    monkeypatch.setattr(diagnostics.windows_emi, "is_emi_available", lambda: False)
    (missing,) = [d for d in diagnose([CPU("cpu_load")]) if d.component == "CPU"]
    assert "requires Windows 11 on bare metal" in missing.reason

    monkeypatch.setattr(diagnostics.windows_emi, "is_emi_available", lambda: True)
    (present,) = [d for d in diagnose([CPU("cpu_load")]) if d.component == "CPU"]
    assert present.reason.endswith("is available but was not selected")

    # Windows has no actionable fix to hand out
    assert missing.fix is None and present.fix is None


def test_unknown_platform_has_no_counter_and_no_fix(monkeypatch):
    _force_platform(monkeypatch)

    (found,) = [d for d in diagnose([CPU("cpu_load")]) if d.component == "CPU"]
    assert found.reason == "no hardware energy counter is supported on this platform"
    assert found.fix is None


def test_windows_emi_mode_is_measured():
    (found,) = [d for d in diagnose([CPU("windows_emi")]) if d.component == "CPU"]
    assert found.status == MEASURED
    assert found.method == "Windows Energy Meter Interface"
    assert found.fix is None


def test_constant_mode_reports_the_constant(monkeypatch):
    _force_platform(monkeypatch)

    (found,) = [d for d in diagnose([CPU("constant", tdp=95)]) if d.component == "CPU"]
    assert found.status == ESTIMATED
    assert found.method == "constant 95 W"


def test_cpu_load_mode_reports_the_tdp(monkeypatch):
    _force_platform(monkeypatch)

    (found,) = [d for d in diagnose([CPU("cpu_load", tdp=95)]) if d.component == "CPU"]
    assert found.method == "CPU load model over a 95 W TDP"


def test_apple_silicon_is_measured_by_powermetrics(monkeypatch):
    monkeypatch.setattr(
        diagnostics.powermetrics, "is_powermetrics_available", lambda: True
    )
    diagnostics_list = diagnose([AppleSiliconChip(chip_part="GPU")])
    (found,) = [d for d in diagnostics_list if d.component == "GPU"]
    assert found.status == MEASURED
    assert found.method == "PowerMetrics"
    assert found.detail == "Apple M2"
    # the Apple GPU counts as a GPU, so no "none detected" entry is appended
    assert len(diagnostics_list) == 1


def test_apple_silicon_without_powermetrics_is_not_reported_as_measured(monkeypatch):
    # a Mac missing the sudoers rule reads nothing; saying MEASURED would be a lie
    monkeypatch.setattr(
        diagnostics.powermetrics, "is_powermetrics_available", lambda: False
    )
    (found,) = [
        d for d in diagnose([AppleSiliconChip(chip_part="CPU")]) if d.component == "CPU"
    ]
    assert found.status == UNAVAILABLE
    assert "passwordless sudo rule" in found.reason
    assert "powermetrics" in found.fix


def test_generic_tdp_is_flagged():
    (found,) = [
        d
        for d in diagnose([CPU("cpu_load", is_generic_tdp=True)])
        if d.component == "CPU"
    ]
    assert "not in the TDP registry" in found.reason


def test_ram_is_always_estimated():
    (found,) = [d for d in diagnose([RAM()]) if d.component == "RAM"]
    assert found.status == ESTIMATED

    (forced,) = [d for d in diagnose([RAM(10)]) if d.component == "RAM"]
    assert "user-provided constant" in forced.method


def test_gpu_measured_and_missing_gpu_reported():
    (found,) = [d for d in diagnose([GPU(["A100", "A100"])]) if d.component == "GPU"]
    assert found.status == MEASURED
    assert found.detail == "2 x A100"

    (missing,) = [d for d in diagnose([RAM()]) if d.component == "GPU"]
    assert missing.status == UNAVAILABLE


def test_gpu_without_a_power_reading_is_not_measured():
    # the driver lists the device but answers "not supported" to the power query
    (found,) = [
        d
        for d in diagnose([GPU(["GTX 1080"], power_usage=None)])
        if d.component == "GPU"
    ]
    assert found.status == UNAVAILABLE
    assert "no power reading" in found.reason
    assert found.detail == "1 x GTX 1080"


def test_report_shape_and_summary():
    report = diagnose([RAM(), CPU("intel_rapl")])
    for component in report:
        assert set(component.as_dict()) == {
            "component",
            "detail",
            "status",
            "method",
            "reason",
            "fix",
        }
        assert component.status in {MEASURED, ESTIMATED, UNAVAILABLE}
    assert summary(report).startswith("1 of 3")
    assert "RAM" in render_text(report)


def test_render_text_shows_status_reason_and_fix():
    report = [
        ComponentDiagnostic(
            "CPU", "Fake CPU", ESTIMATED, "CPU load model", reason="why", fix="do this"
        ),
        ComponentDiagnostic("GPU", "1 x A100", MEASURED, "NVML/AMDSMI"),
    ]
    text = render_text(report)

    assert "[yellow]ESTIMATED[/yellow] - CPU load model" in text
    assert "[green]MEASURED[/green] - NVML/AMDSMI" in text
    assert "    Why: why" in text
    assert "    Fix: do this" in text
    # a component without a reason/fix must not emit empty Why/Fix lines
    assert text.count("Why:") == 1 and text.count("Fix:") == 1
    assert text.endswith(
        "1 of 2 power components are measured directly."
        " Run the fixes above to improve the accuracy of your results."
    )


def test_render_text_escapes_markup_in_hardware_names():
    report = [ComponentDiagnostic("CPU", "Fake [i7] CPU", MEASURED, "RAPL")]
    assert "Fake \\[i7] CPU" in render_text(report)


def test_summary_is_silent_when_everything_is_measured():
    report = [ComponentDiagnostic("CPU", "Fake CPU", MEASURED, "RAPL")]
    assert summary(report) == "1 of 1 power components are measured directly."


HARDWARE_INFO = {
    "ram_total_size": 32.0,
    "cpu_count": 16,
    "cpu_physical_count": 8,
    "cpu_model": "Fake CPU",
    "gpu_count": 0,
    "gpu_model": "",
    "gpu_ids": None,
}


def _patch_detect_hardware(monkeypatch, hardware_list):
    kwargs_seen = {}

    class FakeTracker:
        def __init__(self, *args, **kwargs):
            kwargs_seen.update(kwargs)
            self._hardware = hardware_list

        def get_detected_hardware(self):
            return HARDWARE_INFO

    monkeypatch.setattr("codecarbon.emissions_tracker.EmissionsTracker", FakeTracker)
    return kwargs_seen


def test_detect_allows_multiple_runs(monkeypatch):
    # without it, a live run makes __init__ return early and the hardware setup
    # raises AttributeError on a half-built tracker.
    kwargs_seen = _patch_detect_hardware(monkeypatch, [CPU("intel_rapl")])
    assert CliRunner().invoke(cli_main.codecarbon, ["detect"]).exit_code == 0
    assert kwargs_seen["allow_multiple_runs"] is True


def test_detect_json_output(monkeypatch):
    _patch_detect_hardware(monkeypatch, [RAM(), CPU("intel_rapl")])
    result = CliRunner().invoke(cli_main.codecarbon, ["detect", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert set(payload) == {"codecarbon_version", "hardware", "components", "summary"}
    assert payload["hardware"] == HARDWARE_INFO
    assert payload["codecarbon_version"] == cli_main.__version__
    assert {c["component"] for c in payload["components"]} == {"RAM", "CPU", "GPU"}
    assert payload["summary"].startswith(
        "1 of 3 power components are measured directly."
    )
    cpu = next(c for c in payload["components"] if c["component"] == "CPU")
    assert cpu == {
        "component": "CPU",
        "detail": "Fake CPU",
        "status": MEASURED,
        "method": "RAPL",
        "reason": None,
        "fix": None,
    }


def test_detect_text_output(monkeypatch):
    _patch_detect_hardware(monkeypatch, [RAM(), CPU("intel_rapl")])
    result = CliRunner().invoke(cli_main.codecarbon, ["detect"])
    assert result.exit_code == 0
    assert "Detected Hardware and System Information:" in result.output
    assert "- CPU model: Fake CPU" in result.output
    assert f"CodeCarbon {cli_main.__version__}" in result.output
    assert "RAM" in result.output and "MEASURED" in result.output
    assert "1 of 3 power components are measured directly." in result.output
    # the human report is not JSON
    assert not result.output.lstrip().startswith("{")
