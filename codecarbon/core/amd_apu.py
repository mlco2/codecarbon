"""
Package power of AMD APUs, read from the amdgpu hwmon interface.

On an APU (Ryzen with integrated Radeon, e.g. Strix Halo) the CPU cores, the
iGPU and the rest of the SoC share one power budget, which amdgpu exposes as
socket power ("PPT") in hwmon. That single reading covers both the CPU and the
GPU, so it replaces CPU tracking and the iGPU must not be tracked separately
through amdsmi, which would report the same socket power a second time.

Unlike RAPL, the hwmon power files are world-readable, so this works without
root.
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from codecarbon.external.logger import logger

AMD_PCI_VENDOR = "0x1002"
DRM_ROOT = "/sys/class/drm"
# amdgpu's gpu_metrics layouts: format revision 1 is dGPU, 2 and above are the
# APU layouts (gpu_metrics_v2_x, v3_0 in kgd_pp_interface.h).
MIN_APU_METRICS_FORMAT = 2
# Prefer the instantaneous reading; power1_average is a firmware-smoothed value.
POWER_FILES = ("power1_input", "power1_average")


def _read(path: Path) -> Optional[str]:
    try:
        return path.read_text().strip()
    except OSError:
        return None


def _metrics_format_revision(device: Path) -> Optional[int]:
    try:
        with open(device / "gpu_metrics", "rb") as f:
            header = f.read(4)
    except OSError:
        return None
    # struct metrics_table_header { u16 structure_size; u8 format_revision; u8 content_revision; }
    return header[2] if len(header) == 4 else None


@lru_cache(maxsize=1)
def find_apu_power_file(drm_root: str = DRM_ROOT) -> Optional[Path]:
    """Path of the readable hwmon power file of an AMD APU, or None."""
    root = Path(drm_root)
    if not root.is_dir():
        return None
    for card in sorted(root.iterdir()):
        # card0, card1... but not connectors such as card1-DP-1
        if not re.fullmatch(r"card\d+", card.name):
            continue
        device = card / "device"
        if _read(device / "vendor") != AMD_PCI_VENDOR:
            continue
        revision = _metrics_format_revision(device)
        if revision is None or revision < MIN_APU_METRICS_FORMAT:
            continue
        for hwmon in sorted((device / "hwmon").glob("hwmon*")):
            for name in POWER_FILES:
                path = hwmon / name
                value = _read(path)
                if value is not None and value.isdigit():
                    logger.debug(f"AMD APU package power found at {path}")
                    return path
    return None


def clear_apu_cache() -> None:
    find_apu_power_file.cache_clear()


def is_apu_power_available() -> bool:
    return find_apu_power_file() is not None


def read_apu_power_watts(path: Path) -> float:
    """Current package power in watts (hwmon reports microwatts)."""
    value = _read(path)
    if value is None or not value.isdigit():
        logger.warning(f"Could not read AMD APU power from {path}")
        return 0.0
    return int(value) / 1_000_000
