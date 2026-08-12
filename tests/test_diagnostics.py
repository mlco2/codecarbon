"""Tests for the measurement quality diagnostics and the `codecarbon doctor` CLI."""

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


class CPU:  # named to match the dispatch in diagnose()
    def __init__(self, mode, model="Fake CPU", tdp=65, is_generic_tdp=False):
        self._mode = mode
        self._model = model
        self._tdp = tdp
        self._is_generic_tdp = is_generic_tdp


class RAM:
    def __init__(self, force_ram_power=None):
        self._force_ram_power = force_ram_power
        self.machine_memory_GB = 32.0


class GPU:
    def __init__(self, names):
        self.devices = SimpleNamespace(
            get_gpu_static_info=lambda: [{"name": name} for name in names]
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


def _patch_doctor_hardware(monkeypatch, hardware):
    class FakeTracker:
        def __init__(self, *args, **kwargs):
            self._hardware = hardware

        def _ensure_hardware_ready(self):
            pass

    monkeypatch.setattr("codecarbon.emissions_tracker.EmissionsTracker", FakeTracker)


def test_doctor_json_output(monkeypatch):
    _patch_doctor_hardware(monkeypatch, [RAM(), CPU("intel_rapl")])
    result = CliRunner().invoke(cli_main.codecarbon, ["doctor", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert {c["component"] for c in payload["components"]} == {"RAM", "CPU", "GPU"}


def test_doctor_strict_exit_code(monkeypatch):
    _patch_doctor_hardware(monkeypatch, [RAM(), CPU("cpu_load")])
    assert CliRunner().invoke(cli_main.codecarbon, ["doctor"]).exit_code == 0
    assert (
        CliRunner().invoke(cli_main.codecarbon, ["doctor", "--strict"]).exit_code == 1
    )


def test_doctor_strict_passes_when_all_measured(monkeypatch):
    _patch_doctor_hardware(monkeypatch, [CPU("intel_rapl"), GPU(["A100"])])
    monkeypatch.setattr(
        diagnostics,
        "_ram_diagnostic",
        lambda hw: ComponentDiagnostic("RAM", "32 GB", MEASURED, "fake"),
    )
    result = CliRunner().invoke(cli_main.codecarbon, ["doctor", "--strict"])
    assert result.exit_code == 0
