import platform
import unittest
from unittest.mock import patch, MagicMock
import codecarbon.telemetry as telemetry_module
from codecarbon.telemetry import collect_tier1_payload, send_tier1_telemetry


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


class TestTier1Send(unittest.TestCase):
    def test_send_tier1_telemetry_sends_once_per_session(self):
        """Verify deduplication: second call doesn't POST again."""
        telemetry_module._TIER1_SENT = False  # reset between test runs
        conf = {
            "python_version": "3.11.0",
            "os": "Linux",
            "cpu_count": 4,
            "cpu_model": "Intel i5",
            "gpu_count": 0,
            "gpu_model": None,
            "ram_total_size": 16.0,
            "codecarbon_version": "2.0.0",
            "tracking_mode": "process",
        }
        with patch("codecarbon.telemetry.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=201)
            result = send_tier1_telemetry(conf)
            self.assertTrue(result)
            assert mock_post.call_count == 1
            # second call is deduplicated
            result = send_tier1_telemetry(conf)
            self.assertFalse(result)
            assert mock_post.call_count == 1

    def test_send_tier1_telemetry_fails_silently(self):
        """Verify exceptions are caught and logged, not raised."""
        telemetry_module._TIER1_SENT = False
        conf = {
            "python_version": "3.11.0",
            "os": "Linux",
            "cpu_count": 4,
            "cpu_model": None,
            "gpu_count": 0,
            "gpu_model": None,
            "ram_total_size": 8.0,
            "codecarbon_version": "2.0.0",
            "tracking_mode": "process",
        }
        with patch("codecarbon.telemetry.requests.post", side_effect=Exception("network error")):
            with patch("codecarbon.telemetry.logger.error") as mock_logger:
                # must not raise
                result = send_tier1_telemetry(conf)
                self.assertFalse(result)
                # verify error was logged
                mock_logger.assert_called_once()
                assert "network error" in str(mock_logger.call_args)


if __name__ == "__main__":
    unittest.main()
