"""
Measurement quality diagnostics.

CodeCarbon always produces a number, but depending on the machine that number
may come from a hardware energy counter (RAPL, powermetrics, NVML, ...) or from
a model (CPU load over a TDP, RAM power estimation). This module inspects the
hardware objects the tracker built and reports, per component, whether the
reading is measured or estimated, why, and how to improve it.

It adds no measurement code: it only reads the mode each hardware object landed
in and the availability checks the setup already runs.
"""

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from rich.markup import escape

from codecarbon.core import powermetrics, windows_emi
from codecarbon.core.util import is_linux_os, is_mac_os, is_windows_os

MEASURED = "measured"
ESTIMATED = "estimated"
UNAVAILABLE = "unavailable"

RAPL_DOC = "https://docs.codecarbon.io/how-to/enable-rapl/"
METHODOLOGY_DOC = "https://docs.codecarbon.io/explanation/methodology/"

DEFAULT_RAPL_ROOT = "/sys/class/powercap/intel-rapl"

# CPU modes that read a hardware energy counter.
MEASURED_CPU_MODES = {"intel_rapl", "intel_power_gadget", "windows_emi"}


@dataclass
class ComponentDiagnostic:
    """Measurement quality of a single power component."""

    component: str  # "CPU" | "RAM" | "GPU"
    detail: str  # model name / device list
    status: str  # MEASURED | ESTIMATED | UNAVAILABLE
    method: str  # "RAPL", "PowerMetrics", "CPU load model", ...
    reason: Optional[str] = None  # why a better method was not used
    fix: Optional[str] = None  # concrete command or doc link

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _rapl_reason() -> str:
    """Tell 'no RAPL on this platform' apart from 'RAPL is there but root-only'."""
    if not os.path.exists(DEFAULT_RAPL_ROOT):
        return (
            f"no RAPL interface at {DEFAULT_RAPL_ROOT} (not an Intel/AMD RAPL "
            "platform, or a virtual machine that does not expose it)"
        )
    for dirpath, _, filenames in os.walk(DEFAULT_RAPL_ROOT):
        if "energy_uj" in filenames:
            path = os.path.join(dirpath, "energy_uj")
            if not os.access(path, os.R_OK):
                return (
                    f"{DEFAULT_RAPL_ROOT} exists but {path} is not readable by "
                    "this user (permission denied)"
                )
            return (
                f"{DEFAULT_RAPL_ROOT} is readable but was not selected; run with "
                "--log-level DEBUG to see why"
            )
    return f"{DEFAULT_RAPL_ROOT} exists but exposes no energy counter"


def _rapl_fix() -> str:
    if not os.path.exists(DEFAULT_RAPL_ROOT):
        return f"none available on this platform; see {RAPL_DOC}"
    return f"sudo chmod -R a+r {DEFAULT_RAPL_ROOT} (see {RAPL_DOC} to persist it)"


def _cpu_estimation_reason() -> str:
    """Why no hardware CPU energy counter was used, for the current platform."""
    if is_linux_os():
        return _rapl_reason()
    if is_mac_os():
        if not powermetrics.is_powermetrics_available():
            return (
                "powermetrics is not usable without a password: it needs a "
                "passwordless sudo rule"
            )
        return "powermetrics is available but was not selected"
    if is_windows_os():
        if not windows_emi.is_emi_available():
            return (
                "the Windows Energy Meter Interface is not available; it "
                "requires Windows 11 on bare metal (not a virtual machine)"
            )
        return "the Windows Energy Meter Interface is available but was not selected"
    return "no hardware energy counter is supported on this platform"


def _cpu_estimation_fix() -> Optional[str]:
    if is_linux_os():
        return _rapl_fix()
    if is_mac_os():
        return "allow passwordless sudo for powermetrics, see " f"{METHODOLOGY_DOC}#cpu"
    return None


def _cpu_diagnostic(hw) -> ComponentDiagnostic:
    mode = hw._mode
    detail = hw._model or "unknown CPU"
    if mode in MEASURED_CPU_MODES:
        method = {
            "intel_rapl": "RAPL",
            "intel_power_gadget": "Intel Power Gadget",
            "windows_emi": "Windows Energy Meter Interface",
        }[mode]
        return ComponentDiagnostic(
            component="CPU", detail=detail, status=MEASURED, method=method
        )

    if mode == "constant":
        method = f"constant {hw._tdp} W"
    else:
        method = f"CPU load model over a {hw._tdp} W TDP"
    reason = _cpu_estimation_reason()
    if hw._is_generic_tdp:
        reason = (
            f"CPU model '{detail}' is not in the TDP registry, so a generic "
            f"{hw._tdp} W constant is used; {reason}"
        )
    return ComponentDiagnostic(
        component="CPU",
        detail=detail,
        status=ESTIMATED,
        method=method,
        reason=reason,
        fix=_cpu_estimation_fix(),
    )


def _apple_diagnostic(hw) -> ComponentDiagnostic:
    return ComponentDiagnostic(
        component=hw.chip_part,
        detail=hw._model or "Apple Silicon",
        status=MEASURED,
        method="PowerMetrics",
    )


def _ram_diagnostic(hw) -> ComponentDiagnostic:
    if hw._force_ram_power is not None:
        return ComponentDiagnostic(
            component="RAM",
            detail=f"{hw.machine_memory_GB:.1f} GB",
            status=ESTIMATED,
            method=f"user-provided constant ({hw._force_ram_power} W)",
            reason="force_ram_power is set, so no model and no counter is used",
        )
    return ComponentDiagnostic(
        component="RAM",
        detail=f"{hw.machine_memory_GB:.1f} GB",
        status=ESTIMATED,
        method="RAM power estimation model",
        reason="no platform exposes a DRAM energy counter to CodeCarbon",
        fix=f"none; see {METHODOLOGY_DOC}#ram for the model used",
    )


def _gpu_diagnostic(hw) -> ComponentDiagnostic:
    devices = hw.devices.get_gpu_static_info()
    names = ", ".join(sorted({device["name"] for device in devices})) or "unknown"
    return ComponentDiagnostic(
        component="GPU",
        detail=f"{len(devices)} x {names}",
        status=MEASURED,
        method="NVML/AMDSMI",
    )


def _no_gpu_diagnostic() -> ComponentDiagnostic:
    return ComponentDiagnostic(
        component="GPU",
        detail="none detected",
        status=UNAVAILABLE,
        method="none",
        reason="no NVIDIA GPU (nvidia-ml-py) and no AMD GPU (amdsmi) found",
        fix="if you have a GPU, install the matching extra: pip install codecarbon[gpu]",
    )


def diagnose(hardware) -> List[ComponentDiagnostic]:
    """
    Build a measurement quality report from the hardware objects a tracker set up.

    :param hardware: iterable of BaseHardware instances (``tracker._hardware``).
    """
    diagnostics = []
    for hw in hardware:
        name = type(hw).__name__
        if name == "CPU":
            diagnostics.append(_cpu_diagnostic(hw))
        elif name == "AppleSiliconChip":
            diagnostics.append(_apple_diagnostic(hw))
        elif name == "RAM":
            diagnostics.append(_ram_diagnostic(hw))
        elif name == "GPU":
            diagnostics.append(_gpu_diagnostic(hw))
    if not any(d.component == "GPU" for d in diagnostics):
        diagnostics.append(_no_gpu_diagnostic())
    return diagnostics


def summary(diagnostics: List[ComponentDiagnostic]) -> str:
    measured = sum(1 for d in diagnostics if d.status == MEASURED)
    total = len(diagnostics)
    line = f"{measured} of {total} power components are measured directly."
    if measured < total:
        line += " Run the fixes above to improve the accuracy of your results."
    return line


def render_text(diagnostics: List[ComponentDiagnostic]) -> str:
    """Human readable report, one block per component, with rich markup."""
    lines = []
    for diagnostic in diagnostics:
        lines.append(
            f"[bold]{diagnostic.component}[/bold]  {escape(diagnostic.detail)}"
        )
        colour = {MEASURED: "green", ESTIMATED: "yellow", UNAVAILABLE: "red"}[
            diagnostic.status
        ]
        lines.append(
            f"    [{colour}]{diagnostic.status.upper()}[/{colour}]"
            f" - {escape(diagnostic.method)}"
        )
        if diagnostic.reason:
            lines.append(f"    Why: {escape(diagnostic.reason)}")
        if diagnostic.fix:
            lines.append(f"    Fix: {escape(diagnostic.fix)}")
        lines.append("")
    lines.append(summary(diagnostics))
    return "\n".join(lines)
