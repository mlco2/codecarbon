import unittest
from time import sleep
from unittest import mock

from codecarbon.core.units import Power
from codecarbon.emissions_tracker import OfflineEmissionsTracker
from codecarbon.external.hardware import CPU, MODE_CPU_LOAD


@mock.patch("codecarbon.core.cpu.is_psutil_available", return_value=True)
@mock.patch("codecarbon.core.cpu.is_powergadget_available", return_value=False)
@mock.patch("codecarbon.core.cpu.is_rapl_available", return_value=False)
class TestCPULoad(unittest.TestCase):
    def test_cpu_total_power_process(
        self,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        cpu = CPU.from_utils(
            None,
            MODE_CPU_LOAD,
            "Intel(R) Core(TM) i7-7600U CPU @ 2.80GHz",
            100,
            tracking_mode="process",
        )
        cpu.start()
        sleep(0.5)
        power = cpu._get_power_from_cpu_load()
        self.assertGreaterEqual(power.W, 0.0)

    @mock.patch(
        "codecarbon.external.hardware.CPU._get_power_from_cpu_load",
        return_value=Power.from_watts(50),
    )
    def test_cpu_total_power(
        self,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
        mocked_get_power_from_cpu_load,
    ):
        cpu = CPU.from_utils(
            None, MODE_CPU_LOAD, "Intel(R) Core(TM) i7-7600U CPU @ 2.80GHz", 100
        )
        cpu.start()
        sleep(0.5)
        power = cpu._get_power_from_cpu_load()
        self.assertEqual(power.W, 50)
        self.assertEqual(cpu.total_power().W, 50)

    def test_cpu_load_detection(
        self,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        tracker = OfflineEmissionsTracker(country_iso_code="FRA")
        for hardware in tracker._hardware:
            if isinstance(hardware, CPU) and hardware._mode == MODE_CPU_LOAD:
                break
        else:
            raise Exception("No CPU load !!!")
        tracker.start()
        sleep(0.5)
        emission = tracker.stop()
        self.assertGreater(emission, 0.0)

    def test_cpu_calculate_power_from_cpu_load_threadripper(
        self,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        tdp = 100
        cpu_model = "AMD Ryzen Threadripper 3990X 64-Core Processor"
        cpu = CPU.from_utils(None, MODE_CPU_LOAD, cpu_model, tdp)
        tests_values = [
            {
                "cpu_load": 0.0,
                "expected_power": 0.0,
            },
            {
                "cpu_load": 50,
                "expected_power": 95.0,
            },
            {
                "cpu_load": 100,
                "expected_power": 98.76872502064151,
            },
        ]
        for test in tests_values:
            power = cpu._calculate_power_from_cpu_load(tdp, test["cpu_load"], cpu_model)
            self.assertEqual(power, test["expected_power"])

    def test_cpu_calculate_power_from_cpu_load_linear(
        self,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        tdp = 100
        cpu_model = "Random Processor"
        cpu = CPU.from_utils(None, MODE_CPU_LOAD, cpu_model, tdp)
        tests_values = [
            {
                "cpu_load": 0.0,
                "expected_power": tdp * 0.1,
            },
            {
                "cpu_load": 50,
                "expected_power": 50.0,
            },
            {
                "cpu_load": 100,
                "expected_power": 100.0,
            },
        ]
        for test in tests_values:
            power = cpu._calculate_power_from_cpu_load(tdp, test["cpu_load"], cpu_model)
            self.assertEqual(power, test["expected_power"])
