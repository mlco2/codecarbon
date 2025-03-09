"""Tests for the Raspberry Pi power interface (`vcgencmd pmic_read_adc`)."""

import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from codecarbon.core import cpu
from codecarbon.core.units import Energy, Power, Time, Water

# Shape of `vcgencmd pmic_read_adc`, with round values so the expected power is
# obvious: every rail draws current x volt watts. HDMI has no volt reading and
# EXT5V no current one, as on a real Pi, so both are skipped.
PMIC_OUTPUT = b"""\
        3V7_WL_SW_A current(0)=1.00000000A
         3V3_SYS_A current(1)=2.00000000A
        VDD_CORE_A current(7)=3.00000000A
        DDR_VDD2_A current(3)=4.00000000A
            HDMI_A current(11)=5.00000000A
        3V7_WL_SW_V volt(16)=1.00000000V
         3V3_SYS_V volt(17)=2.00000000V
        VDD_CORE_V volt(23)=3.00000000V
        DDR_VDD2_V volt(19)=4.00000000V
           EXT5V_V volt(24)=5.00000000V
"""

# 3V7_WL_SW + 3V3_SYS + VDD_CORE, the wanted CPU rails: 1x1 + 2x2 + 3x3
CPU_WATTS = 14.0
# DDR_VDD2, the only wanted memory rail present: 4x4
RAM_WATTS = 16.0


@pytest.fixture
def raspberry_cls():
    """The Raspberry class the tracker itself uses.

    Other tests drop codecarbon.external.hardware from sys.modules, so the
    class must be looked up at call time, not at import time.
    """
    from codecarbon.emissions_tracker import Raspberry

    return Raspberry


@pytest.fixture
def make_raspberry(raspberry_cls):
    def _make(chip_part="CPU"):
        return raspberry_cls(
            output_dir="out", model="Raspberry Pi 5", chip_part=chip_part
        )

    return _make


@pytest.fixture
def hardware_globals(raspberry_cls):
    """Module globals of the hardware module that class was defined in."""
    return raspberry_cls.get_measure.__globals__


@pytest.fixture
def mock_vcgencmd(hardware_globals):
    """Patch the vcgencmd call, yielding the mock so callers can assert on it."""
    mock_run = MagicMock(return_value=SimpleNamespace(stdout=PMIC_OUTPUT))
    with patch.dict(hardware_globals, {"run": mock_run}):
        yield mock_run


def test_is_raspberry_detects_vcgencmd():
    with patch("codecarbon.core.cpu.os.path.exists", return_value=True) as mock_exists:
        assert cpu.is_raspberry() is True
    mock_exists.assert_called_once_with("/usr/bin/vcgencmd")


def test_is_raspberry_false_without_vcgencmd():
    with patch("codecarbon.core.cpu.os.path.exists", return_value=False):
        assert cpu.is_raspberry() is False


def test_cpu_chip_part_wants_core_rails(make_raspberry):
    raspberry = make_raspberry("CPU")
    assert "VDD_CORE" in raspberry.WANTED_COMPONENTS
    assert "DDR_VDD2" not in raspberry.WANTED_COMPONENTS


def test_ram_chip_part_wants_memory_rails(make_raspberry):
    raspberry = make_raspberry("RAM")
    assert "DDR_VDDQ" in raspberry.WANTED_COMPONENTS
    assert "VDD_CORE" not in raspberry.WANTED_COMPONENTS


def test_unknown_chip_part_is_rejected(make_raspberry):
    with pytest.raises(Exception, match="Unknown chip part"):
        make_raspberry("GPU")


def test_repr_names_model_and_chip_part(make_raspberry):
    assert repr(make_raspberry("RAM")) == "Raspberry (Raspberry Pi 5 > RAM)"


def test_get_model_returns_detected_model(make_raspberry):
    assert make_raspberry().get_model() == "Raspberry Pi 5"


def test_get_measure_runs_vcgencmd(make_raspberry, mock_vcgencmd):
    make_raspberry().get_measure()
    mock_vcgencmd.assert_called_once_with(
        ["vcgencmd", "pmic_read_adc"], capture_output=True
    )


def test_get_measure_sums_cpu_rails(make_raspberry, mock_vcgencmd):
    assert make_raspberry("CPU").get_measure() == {"power": CPU_WATTS}


def test_get_measure_sums_memory_rails(make_raspberry, mock_vcgencmd):
    assert make_raspberry("RAM").get_measure() == {"power": RAM_WATTS}


def test_total_power_reads_the_pmic(make_raspberry, mock_vcgencmd):
    assert make_raspberry().total_power() == Power.from_watts(CPU_WATTS)


def test_get_energy_scales_power_over_time(make_raspberry, mock_vcgencmd):
    energy = make_raspberry()._get_energy(Time.from_seconds(3600).seconds)
    assert energy.kWh == pytest.approx(CPU_WATTS / 1000)


def test_measure_power_and_energy_over_a_duration(make_raspberry, mock_vcgencmd):
    power, energy = make_raspberry().measure_power_and_energy(last_duration=3600)
    assert power == Power.from_watts(CPU_WATTS)
    assert energy.kWh == pytest.approx(CPU_WATTS / 1000)


def test_from_utils_detects_the_model(raspberry_cls, hardware_globals):
    with patch.dict(hardware_globals, {"detect_cpu_model": lambda: "Raspberry Pi 5"}):
        raspberry = raspberry_cls.from_utils("out")
    assert raspberry.get_model() == "Raspberry Pi 5"
    assert raspberry.chip_part == "CPU"
    assert raspberry._output_dir == "out"


def test_from_utils_keeps_an_explicit_model(raspberry_cls, hardware_globals):
    mock_detect = MagicMock()
    with patch.dict(hardware_globals, {"detect_cpu_model": mock_detect}):
        raspberry = raspberry_cls.from_utils(
            "out", model="Raspberry Pi 4", chip_part="RAM"
        )
    mock_detect.assert_not_called()
    assert raspberry.get_model() == "Raspberry Pi 4"
    assert raspberry.chip_part == "RAM"


def test_from_utils_warns_when_the_model_is_unknown(raspberry_cls, hardware_globals):
    mock_logger = MagicMock()
    with patch.dict(
        hardware_globals,
        {"detect_cpu_model": lambda: None, "logger": mock_logger},
    ):
        raspberry = raspberry_cls.from_utils("out")
    assert raspberry.get_model() is None
    mock_logger.warning.assert_called_once()


def make_measurement_state(hardware):
    """Minimal tracker state for BaseEmissionsTracker._do_measurements."""
    return SimpleNamespace(
        _hardware=[hardware],
        _last_measured_time=time.perf_counter() - 3600,
        _pue=1.0,
        _wue=0.0,
        _total_energy=Energy.from_energy(kWh=0),
        _total_water=Water.from_litres(litres=0),
        _total_cpu_energy=Energy.from_energy(kWh=0),
        _total_ram_energy=Energy.from_energy(kWh=0),
        _cpu_power=Power.from_watts(0),
        _ram_power=Power.from_watts(0),
        _power_measurement_count=0,
    )


def test_do_measurements_credits_cpu_energy(make_raspberry, mock_vcgencmd):
    from codecarbon.emissions_tracker import BaseEmissionsTracker

    tracker = make_measurement_state(make_raspberry("CPU"))

    BaseEmissionsTracker._do_measurements(tracker)

    assert tracker._cpu_power == Power.from_watts(CPU_WATTS)
    assert tracker._total_cpu_energy.kWh == pytest.approx(CPU_WATTS / 1000, rel=1e-3)
    assert tracker._total_ram_energy.kWh == 0
    assert tracker._power_measurement_count == 1


def test_do_measurements_credits_ram_energy(make_raspberry, mock_vcgencmd):
    from codecarbon.emissions_tracker import BaseEmissionsTracker

    tracker = make_measurement_state(make_raspberry("RAM"))

    BaseEmissionsTracker._do_measurements(tracker)

    assert tracker._ram_power == Power.from_watts(RAM_WATTS)
    assert tracker._total_ram_energy.kWh == pytest.approx(RAM_WATTS / 1000, rel=1e-3)
    assert tracker._total_cpu_energy.kWh == 0
