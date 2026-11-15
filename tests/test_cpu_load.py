import threading
import unittest
from time import sleep
from unittest import mock

from codecarbon.core.units import Power
from codecarbon.emissions_tracker import OfflineEmissionsTracker
from codecarbon.external.hardware import (
    CPU,
    MODE_CPU_LOAD,
    AppleSiliconChip,
    SystemCPULoadMeter,
)


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

    @mock.patch("codecarbon.core.windows_emi.is_emi_available", return_value=False)
    @mock.patch(
        "codecarbon.core.powermetrics.is_powermetrics_available", return_value=False
    )
    def test_cpu_load_detection(
        self,
        mocked_is_powermetrics_available,
        mocked_is_emi_available,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        tracker = OfflineEmissionsTracker(country_iso_code="FRA")
        tracker._ensure_hardware_ready()
        for hardware in tracker._hardware:
            if (
                isinstance(hardware, CPU) and hardware._mode == MODE_CPU_LOAD
            ) or isinstance(hardware, AppleSiliconChip):
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

    @mock.patch(
        "codecarbon.external.hardware.CPU._get_power_from_cpus",
        return_value=Power.from_watts(0),
    )
    def test_cpu_total_power_empty_history(
        self,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
        mocked_get_power_from_cpus,
    ):
        """Regression test for issue #832: ZeroDivisionError when no power samples collected."""
        cpu = CPU.from_utils(
            None, MODE_CPU_LOAD, "Intel(R) Core(TM) i7-7600U CPU @ 2.80GHz", 100
        )
        # Simulate an empty power history before calling total_power
        cpu._power_history = []
        result = cpu.total_power()
        # Should NOT raise ZeroDivisionError, should return a valid Power object
        self.assertIsInstance(result, Power)
        self.assertEqual(result.W, 0)

    @mock.patch(
        "codecarbon.external.hardware.CPU._get_power_from_cpus",
        return_value=Power.from_watts(42),
    )
    def test_cpu_total_power_fetches_sample_when_history_is_empty(
        self,
        mocked_get_power_from_cpus,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        """Calling total_power should always fetch the latest sample before averaging."""
        cpu = CPU.from_utils(
            None, MODE_CPU_LOAD, "Intel(R) Core(TM) i7-7600U CPU @ 2.80GHz", 100
        )
        cpu._power_history = []
        result = cpu.total_power()
        self.assertEqual(result.W, 42)
        mocked_get_power_from_cpus.assert_called_once()
        self.assertEqual(cpu._power_history, [])

    def test_cpu_sample_added_while_draining_goes_to_next_window(
        self,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        """A monitor sample that lands while total_power averages the drained
        history is counted in the next window, not lost (see issue #1315)."""
        cpu = CPU.from_utils(
            None, MODE_CPU_LOAD, "Intel(R) Core(TM) i7-7600U CPU @ 2.80GHz", 100
        )

        class HistorySampledWhileRead(list):
            monitor_ran = False

            def __iter__(self):
                if not HistorySampledWhileRead.monitor_ran:
                    HistorySampledWhileRead.monitor_ran = True
                    # Run in another thread: a deadlock here means total_power
                    # holds the lock while reading the drained history.
                    monitor = threading.Thread(target=cpu.monitor_power)
                    monitor.start()
                    monitor.join(5)
                    assert not monitor.is_alive(), "monitor_power was blocked"
                return super().__iter__()

        cpu._power_history = HistorySampledWhileRead([(Power.from_watts(10), 0.0)])
        samples = [Power.from_watts(w) for w in (1, 100, 1)]
        with (
            mock.patch.object(cpu, "_get_power_from_cpus", side_effect=samples),
            mock.patch(
                "codecarbon.external.hardware.time.perf_counter", side_effect=[0, 1, 2]
            ),
        ):
            first = cpu.total_power()  # [10] plus latest 1
            second = cpu.total_power()  # monitor's 100 plus latest 1

        self.assertTrue(HistorySampledWhileRead.monitor_ran)
        self.assertEqual(first.W, (10 + 1) / 2)
        self.assertEqual(second.W, (100 + 1) / 2)
        self.assertEqual(cpu._power_history, [])

    def test_cpu_total_power_and_monitor_power_never_sample_concurrently(
        self,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        """Sampling mutates state in some modes (process tracking deltas, Intel
        Power Gadget log file), so both threads must take turns."""
        cpu = CPU.from_utils(
            None, MODE_CPU_LOAD, "Intel(R) Core(TM) i7-7600U CPU @ 2.80GHz", 100
        )
        counter_lock = threading.Lock()
        active = 0
        max_active = 0

        def slow_sample():
            nonlocal active, max_active
            with counter_lock:
                active += 1
                max_active = max(max_active, active)
            sleep(0.005)
            with counter_lock:
                active -= 1
            return Power.from_watts(1)

        def run(target):
            for _ in range(20):
                target()

        with mock.patch.object(cpu, "_get_power_from_cpus", side_effect=slow_sample):
            threads = [
                threading.Thread(target=run, args=(cpu.monitor_power,)),
                threading.Thread(target=run, args=(cpu.total_power,)),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(10)

        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(max_active, 1)

    @mock.patch(
        "codecarbon.external.hardware.CPU._get_power_from_cpus",
        return_value=Power.from_watts(5),
    )
    def test_cpu_start_discards_samples_from_before_the_window(
        self,
        mocked_get_power_from_cpus,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        cpu = CPU.from_utils(
            None, MODE_CPU_LOAD, "Intel(R) Core(TM) i7-7600U CPU @ 2.80GHz", 100
        )
        cpu._power_history = [(Power.from_watts(500), 1.0)]

        cpu.start()

        self.assertEqual(cpu._power_history, [])
        self.assertEqual(cpu.total_power().W, 5)

    @mock.patch(
        "codecarbon.external.hardware.CPU._get_power_from_cpus",
        return_value=Power.from_watts(30),
    )
    def test_cpu_total_power_averages_buffered_and_latest_sample(
        self,
        mocked_get_power_from_cpus,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        cpu = CPU.from_utils(
            None, MODE_CPU_LOAD, "Intel(R) Core(TM) i7-7600U CPU @ 2.80GHz", 100
        )
        cpu._power_history = [(Power.from_watts(10), 0.0), (Power.from_watts(20), 0.0)]

        result = cpu.total_power()

        self.assertEqual(result.W, 20)
        self.assertEqual(cpu._power_history, [])
        mocked_get_power_from_cpus.assert_called_once()

    @mock.patch(
        "codecarbon.external.hardware.CPU._get_power_from_cpus",
        return_value=Power.from_watts(50),
    )
    def test_cpu_total_power_weights_samples_by_covered_time(
        self,
        mocked_get_power_from_cpus,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        """A latest sample covering a few milliseconds must not weigh as much as
        a monitor sample covering a whole second."""
        cpu = CPU.from_utils(
            None, MODE_CPU_LOAD, "Intel(R) Core(TM) i7-7600U CPU @ 2.80GHz", 100
        )
        cpu._power_history = [(Power.from_watts(10), 3.0)]
        cpu._last_sample_time = 10.0

        with mock.patch(
            "codecarbon.external.hardware.time.perf_counter", return_value=11.0
        ):
            result = cpu.total_power()

        self.assertEqual(result.W, (10 * 3 + 50 * 1) / 4)

    def test_cpu_load_meter_busy_time_excludes_idle_iowait_and_guest(
        self,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        from collections import namedtuple

        Times = namedtuple(
            "Times", "user nice system idle iowait irq softirq steal guest guest_nice"
        )
        before = Times(10, 0, 5, 80, 5, 0, 0, 0, 2, 0)
        after = Times(40, 0, 15, 120, 15, 0, 0, 0, 12, 0)
        meter = SystemCPULoadMeter()
        meter._last_times = before
        with mock.patch(
            "codecarbon.external.hardware.psutil.cpu_times", return_value=after
        ):
            percent = meter.percent()

        # busy: user 30 + system 10 = 40, total without guest: 40 + 40 + 10 = 90
        self.assertAlmostEqual(percent, 40 / 90 * 100)

    def test_cpu_start_sets_process_cpu_time_baseline(
        self,
        mocked_is_psutil_available,
        mocked_is_powergadget_available,
        mocked_is_rapl_available,
    ):
        """In process mode the first sample after start() covers the time since
        start(), instead of reporting 0 W."""
        cpu = CPU.from_utils(
            None,
            MODE_CPU_LOAD,
            "Intel(R) Core(TM) i7-7600U CPU @ 2.80GHz",
            100,
            tracking_mode="process",
        )
        with (
            mock.patch.object(
                cpu, "_get_process_cpu_times", side_effect=[{1: 10.0}, {1: 10.5}]
            ),
            mock.patch(
                "codecarbon.external.hardware.time.time", side_effect=[100.0, 101.0]
            ),
        ):
            cpu.start()
            power = cpu._get_power_from_cpu_load()

        # 0.5 s of CPU time over 1 s of wall time, normalized by the core count
        self.assertAlmostEqual(power.W, 100 * 50 / cpu._cpu_count / 100)
