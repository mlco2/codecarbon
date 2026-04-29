import platform
import unittest
from codecarbon.telemetry import collect_tier1_payload


class TestTelemetry(unittest.TestCase):
    def test_collect_tier1_payload_has_required_fields(self):
        conf = {
            "python_version": platform.python_version(),
            "os": platform.platform(),
            "cpu_count": 8,
            "cpu_model": "Intel Core i7",
            "gpu_count": 1,
            "gpu_model": "NVIDIA RTX 3080",
            "ram_total_size": 32.0,
            "codecarbon_version": "2.0.0",
            "tracking_mode": "machine",
        }
        payload = collect_tier1_payload(conf)
        self.assertIn("python_version", payload)
        self.assertIn("os", payload)
        self.assertIn("cpu_count", payload)
        self.assertIn("cpu_model", payload)
        self.assertIn("gpu_count", payload)
        self.assertIn("gpu_model", payload)
        self.assertIn("ram_total_size", payload)
        self.assertIn("codecarbon_version", payload)
        self.assertIn("tracking_mode", payload)
        self.assertEqual(payload["python_version"], conf["python_version"])


if __name__ == "__main__":
    unittest.main()
