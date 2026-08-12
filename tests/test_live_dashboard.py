import json
import socket
import threading
import unittest
import urllib.error
import urllib.request

from codecarbon.output_methods.emissions_data import EmissionsData
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


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status, response.read()


class TestLiveDashboardOutput(unittest.TestCase):
    def setUp(self):
        # Port 0 lets the OS pick a free port, so tests never collide.
        self.output = LiveDashboardOutput(port=0, history=5)
        self.addCleanup(self.output.exit)

    def test_live_out_appends_and_respects_maxlen(self):
        for i in range(15):
            self.output.live_out(_make_emissions_data(duration=float(i)), None)

        samples = json.loads(self.output._snapshot())["samples"]
        self.assertEqual(5, len(samples))
        self.assertEqual(
            [10.0, 11.0, 12.0, 13.0, 14.0], [s["duration"] for s in samples]
        )

    def test_data_endpoint_returns_expected_payload(self):
        self.output.live_out(_make_emissions_data(), None)

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
                self.output.live_out(_make_emissions_data(), None)

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
            # `live_out_every_measure` opt-in nothing would arrive for minutes.
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
            output.live_out(_make_emissions_data(), None)
            self.assertEqual(1, len(json.loads(output._snapshot())["samples"]))
