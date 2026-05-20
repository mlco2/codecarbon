import unittest
from unittest.mock import patch

import requests_mock
from pydantic import ValidationError

from codecarbon.core.telemetry_client import post_private_telemetry
from codecarbon.core.telemetry_schemas import TelemetryCreate


class TestPostPrivateTelemetry(unittest.TestCase):
    def test_post_private_telemetry_sends_validated_payload(self):
        telemetry = {
            "timestamp": "2026-05-03T12:00:00+00:00",
            "telemetry_level": "minimal",
            "os": "Linux-5.10.0-x86_64",
        }

        with requests_mock.Mocker() as m:
            m.post(
                "http://test.com/telemetry",
                json="f52fe339-164d-4c2b-a8c0-f562dfce066d",
                status_code=201,
            )
            result = post_private_telemetry("http://test.com", telemetry, None)

            self.assertTrue(result)
            self.assertEqual(m.call_count, 1)
            self.assertEqual(
                m.last_request.json(),
                {
                    **telemetry,
                    "timestamp": "2026-05-03T12:00:00Z",
                },
            )

    def test_post_private_telemetry_rejects_invalid_payload(self):
        with self.assertRaises(ValidationError):
            post_private_telemetry(
                "http://test.com",
                {
                    "timestamp": "2026-05-03T12:00:00+00:00",
                    "telemetry_level": "minimal",
                    "unknown_field": "value",
                },
                None,
            )

    def test_post_private_telemetry_logs_warning_on_404(self):
        telemetry = {
            "timestamp": "2026-05-03T12:00:00+00:00",
            "telemetry_level": "minimal",
        }
        with requests_mock.Mocker() as m:
            m.post(
                "http://test.com/telemetry",
                text='{"detail":"Not Found"}',
                status_code=404,
            )
            with patch("codecarbon.core.telemetry_client.logger") as mock_logger:
                result = post_private_telemetry("http://test.com", telemetry, None)
        self.assertFalse(result)
        mock_logger.warning.assert_called_once()

    def test_post_private_telemetry_sends_api_key_header_when_configured(self):
        telemetry = {
            "timestamp": "2026-05-03T12:00:00+00:00",
            "telemetry_level": "minimal",
        }
        with requests_mock.Mocker() as m:
            m.post(
                "http://test.com/telemetry",
                json="telemetry-id",
                status_code=201,
            )
            post_private_telemetry("http://test.com", telemetry, "cpt_test_key")
        self.assertEqual(m.last_request.headers["x-api-token"], "cpt_test_key")

    def test_post_private_telemetry_returns_false_on_request_error(self):
        telemetry = {
            "timestamp": "2026-05-03T12:00:00+00:00",
            "telemetry_level": "minimal",
        }
        with patch("codecarbon.core.telemetry_client.requests.post") as mock_post:
            mock_post.side_effect = ConnectionError("network down")
            with patch("codecarbon.core.telemetry_client.logger"):
                result = post_private_telemetry("http://test.com", telemetry, None)
        self.assertFalse(result)
