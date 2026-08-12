import dataclasses
import json
import socket
import threading
import unittest
import urllib.error
import urllib.request

from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData, TaskEmissionsData
from codecarbon.viz.live import LiveDashboardOutput


def _make_emissions_data(**overrides) -> EmissionsData:
    defaults = dict(
        timestamp="2025-01-15T10:30:00",
        project_name="test_project",
        run_id="550e8400-e29b-41d4-a716-446655440000",
        experiment_id="exp-001",
        duration=3600.0,
        emissions=0.042,
        emissions_rate=1.17e-05,
        cpu_power=12.5,
        gpu_power=85.0,
        ram_power=3.2,
        cpu_energy=0.0125,
        gpu_energy=0.085,
        ram_energy=0.0032,
        energy_consumed=0.1007,
        water_consumed=0.0,
        country_name="France",
        country_iso_code="FRA",
        region="Ile-de-France",
        cloud_provider="",
        cloud_region="",
        os="Linux-5.15.0",
        python_version="3.11.5",
        codecarbon_version="2.5.0",
        cpu_count=8,
        cpu_model="Intel Core i7-12700",
        gpu_count=1,
        gpu_model="NVIDIA RTX 3090",
        longitude=2.3522,
        latitude=48.8566,
        ram_total_size=32.0,
        tracking_mode="machine",
    )
    defaults.update(overrides)
    return EmissionsData(**defaults)


def _make_task_emissions_data(**overrides) -> TaskEmissionsData:
    fields = {f.name for f in dataclasses.fields(TaskEmissionsData)}
    defaults = {
        k: v
        for k, v in dataclasses.asdict(_make_emissions_data()).items()
        if k in fields
    }
    defaults["task_name"] = "a_task"
    defaults.update(overrides)
    return TaskEmissionsData(**defaults)


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status, response.read()


class TestLiveDashboardOutput(unittest.TestCase):
    def setUp(self):
        # Port 0 lets the OS pick a free port, so tests never collide.
        self.output = LiveDashboardOutput(port=0, history=5)
        self.addCleanup(self.output.exit)

    def test_on_measure_appends_and_respects_maxlen(self):
        for i in range(15):
            self.output.on_measure(_make_emissions_data(duration=float(i)))

        samples = json.loads(self.output._snapshot())["samples"]
        self.assertEqual(5, len(samples))
        self.assertEqual(
            [10.0, 11.0, 12.0, 13.0, 14.0], [s["duration"] for s in samples]
        )

    def test_data_endpoint_returns_expected_payload(self):
        self.output.on_measure(_make_emissions_data())

        status, body = _get(f"{self.output.url}/data")
        payload = json.loads(body)

        self.assertEqual(200, status)
        self.assertEqual(1, len(payload["samples"]))
        sample = payload["samples"][0]
        self.assertEqual(12.5, sample["cpu_power"])
        self.assertEqual(85.0, sample["gpu_power"])
        self.assertAlmostEqual(42.0, sample["emissions_g"])
        self.assertEqual("NVIDIA RTX 3090", payload["metadata"]["gpu_model"])
        self.assertEqual([], payload["tasks"])

    def test_index_serves_html_and_unknown_path_is_404(self):
        status, body = _get(self.output.url + "/")
        self.assertEqual(200, status)
        self.assertIn(b"CodeCarbon", body)

        with self.assertRaises(urllib.error.HTTPError) as context:
            _get(f"{self.output.url}/nope")
        self.assertEqual(404, context.exception.code)

    def test_health_endpoint(self):
        status, body = _get(f"{self.output.url}/health")
        self.assertEqual(200, status)
        self.assertEqual({"status": "ok"}, json.loads(body))

    def test_concurrent_reads_and_writes_return_valid_json(self):
        errors = []
        stop = threading.Event()

        def write():
            while not stop.is_set():
                self.output.on_measure(_make_emissions_data())

        def read():
            try:
                for _ in range(20):
                    json.loads(_get(f"{self.output.url}/data")[1])
            except Exception as e:  # pragma: no cover - only on failure
                errors.append(e)

        writer = threading.Thread(target=write, daemon=True)
        writer.start()
        readers = [threading.Thread(target=read) for _ in range(4)]
        for reader in readers:
            reader.start()
        for reader in readers:
            reader.join()
        stop.set()
        writer.join()

        self.assertEqual([], errors)

    def test_exit_releases_the_port(self):
        port = self.output.port
        self.output.exit()

        with socket.socket() as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", port))

    def test_tracker_feeds_a_sample_on_every_measure(self):
        from codecarbon.emissions_tracker import OfflineEmissionsTracker

        tracker = OfflineEmissionsTracker(
            country_iso_code="FRA",
            measure_power_secs=1,
            api_call_interval=30,
            save_to_file=False,
            output_handlers=[self.output],
            allow_multiple_runs=True,
        )
        tracker.start()
        try:
            # Two measures, well below api_call_interval: without the
            # `on_measure` opt-in nothing would arrive for minutes.
            tracker._measure_power_and_energy()
            tracker._measure_power_and_energy()
            samples = json.loads(self.output._snapshot())["samples"]
        finally:
            tracker.stop()

        self.assertGreaterEqual(len(samples), 2)

    def test_busy_port_does_not_raise(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            sock.listen(1)
            busy_port = sock.getsockname()[1]

            output = LiveDashboardOutput(port=busy_port)
            self.addCleanup(output.exit)

            self.assertFalse(output.is_serving)
            # Still usable as an output handler, it just serves nothing.
            output.on_measure(_make_emissions_data())
            self.assertEqual(1, len(json.loads(output._snapshot())["samples"]))

    def test_only_on_measure_feeds_the_history(self):
        # `out` and `live_out` carry power averaged since start(); mixing them
        # into the chart would put incomparable points on the same line.
        self.output.out(_make_emissions_data(duration=7.0), None)
        self.output.live_out(_make_emissions_data(duration=8.0), None)

        samples = json.loads(_get(f"{self.output.url}/data")[1])["samples"]
        self.assertEqual([], samples)

    def test_task_out_is_served_on_the_data_endpoint(self):
        self.output.task_out(
            [_make_task_emissions_data(task_name="train", emissions=0.5)],
            "experiment",
        )

        tasks = json.loads(_get(f"{self.output.url}/data")[1])["tasks"]
        self.assertEqual(1, len(tasks))
        self.assertEqual("train", tasks[0]["task_name"])
        self.assertEqual(0.5, tasks[0]["emissions"])

        # A second call replaces the previous list rather than appending to it.
        self.output.task_out(
            [_make_task_emissions_data(task_name="eval")], "experiment"
        )
        tasks = json.loads(_get(f"{self.output.url}/data")[1])["tasks"]
        self.assertEqual(["eval"], [t["task_name"] for t in tasks])

    def test_binding_outside_loopback_warns_about_the_open_port(self):
        with self.assertLogs("codecarbon", level="WARNING") as logs:
            output = LiveDashboardOutput(port=0, host="0.0.0.0")
            self.addCleanup(output.exit)

        self.assertTrue(output.is_serving)
        self.assertTrue(
            any("not authenticated" in message for message in logs.output),
            logs.output,
        )

    def test_exit_is_idempotent(self):
        self.output.exit()
        self.output.exit()
        self.assertFalse(self.output.is_serving)

    def test_data_is_served_after_the_os_assigned_the_port(self):
        # port=0 means the OS picks: the handler must report the real port, not 0.
        self.assertNotEqual(0, self.output.port)
        self.assertEqual(f"http://127.0.0.1:{self.output.port}", self.output.url)
        self.assertEqual(200, _get(f"{self.output.url}/health")[0])


class _RecordingOutput(BaseOutput):
    """Plain handler: fed only every `api_call_interval` measures."""

    def __init__(self):
        self.calls = []

    def live_out(self, total, delta):
        self.calls.append((total, delta))


class _RecordingLiveOutput(_RecordingOutput):
    """Opt-in handler: defining `on_measure` gets it fed on every measure."""

    def __init__(self):
        super().__init__()
        self.measures = []

    def on_measure(self, total):
        self.measures.append(total)


class TestLiveOutEveryMeasure(unittest.TestCase):
    """The tracker must not feed an every-measure handler twice on an API tick."""

    def _tracker(self, handlers, api_call_interval):
        from codecarbon.emissions_tracker import OfflineEmissionsTracker

        tracker = OfflineEmissionsTracker(
            country_iso_code="FRA",
            measure_power_secs=1,
            api_call_interval=api_call_interval,
            save_to_file=False,
            output_handlers=handlers,
            allow_multiple_runs=True,
        )
        tracker.start()
        self.addCleanup(tracker.stop)
        # `start()` takes a first measure: ignore it so the counts below are exact.
        tracker._measure_occurrence = 0
        for handler in handlers:
            handler.calls.clear()
            getattr(handler, "measures", []).clear()
        return tracker

    def test_on_measure_is_called_every_measure_and_live_out_stays_periodic(self):
        live, plain = _RecordingLiveOutput(), _RecordingOutput()
        tracker = self._tracker([live, plain], api_call_interval=3)

        tracker._measure_power_and_energy()
        tracker._measure_power_and_energy()

        # Below api_call_interval: only the `on_measure` opt-in has been fed.
        self.assertEqual(2, len(live.measures))
        self.assertEqual([], live.calls)
        self.assertEqual([], plain.calls)

        tracker._measure_power_and_energy()

        # The API tick feeds `live_out` on every handler, with a delta.
        self.assertEqual(3, len(live.measures))
        self.assertEqual(1, len(live.calls))
        self.assertEqual(1, len(plain.calls))
        self.assertIsNotNone(plain.calls[0][1])

    def test_on_measure_receives_instantaneous_power_not_the_average(self):
        live = _RecordingLiveOutput()
        tracker = self._tracker([live], api_call_interval=-1)

        # The tracker keeps running sums to compute the averages that
        # EmissionsData carries. Poison them so an average is unmistakably
        # different from the last measured power.
        tracker._cpu_power_sum = 10_000.0
        tracker._gpu_power_sum = 20_000.0
        tracker._ram_power_sum = 30_000.0
        tracker._power_measurement_count = 100

        tracker._measure_power_and_energy()

        sample = live.measures[-1]
        self.assertEqual(tracker._cpu_power.W, sample.cpu_power)
        self.assertEqual(tracker._gpu_power.W, sample.gpu_power)
        self.assertEqual(tracker._ram_power.W, sample.ram_power)
        # ... and the averages the periodic path would have reported are the
        # poisoned ones, so the two are genuinely distinguishable here.
        averaged = tracker._prepare_emissions_data()
        self.assertGreater(averaged.cpu_power, 90.0)
        self.assertLess(sample.cpu_power, 90.0)
