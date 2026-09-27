import time
import unittest
from unittest.mock import patch

import requests_mock
from pydantic import ValidationError

from codecarbon.core.telemetry.client import post_private
from codecarbon.core.telemetry.schemas import TelemetryLevel
from codecarbon.core.telemetry.settings import TelemetrySettings

TELEMETRY = {
    "timestamp": "2026-05-03T12:00:00+00:00",
    "telemetry_level": "minimal",
    "os": "Linux-5.10.0-x86_64",
}


def _settings(api_url: str = "http://test.com") -> TelemetrySettings:
    return TelemetrySettings(
        level=TelemetryLevel.minimal, is_explicit=False, api_url=api_url
    )


class TestPostPrivate(unittest.TestCase):
    def test_post_private_sends_validated_payload_without_token(self):
        with requests_mock.Mocker() as m:
            m.post(
                "http://test.com/telemetry",
                json="f52fe339-164d-4c2b-a8c0-f562dfce066d",
                status_code=201,
            )
            result = post_private(_settings(), TELEMETRY)

            self.assertTrue(result)
            self.assertEqual(m.call_count, 1)
            self.assertEqual(
                m.last_request.json(),
                {**TELEMETRY, "timestamp": "2026-05-03T12:00:00Z"},
            )
            self.assertNotIn("x-api-token", m.last_request.headers)

    def test_post_private_rejects_invalid_payload(self):
        with self.assertRaises(ValidationError):
            post_private(_settings(), {**TELEMETRY, "unknown_field": "value"})

    def test_post_private_logs_debug_on_non_201(self):
        for status_code in (404, 429, 500):
            with self.subTest(status_code=status_code):
                with requests_mock.Mocker() as m:
                    m.post(
                        "http://test.com/telemetry",
                        text="nope",
                        status_code=status_code,
                    )
                    with patch(
                        "codecarbon.core.telemetry.client.logger"
                    ) as mock_logger:
                        result = post_private(_settings(), TELEMETRY)
                self.assertFalse(result)
                mock_logger.debug.assert_called_once()
                mock_logger.warning.assert_not_called()

    def test_post_private_returns_false_on_request_error(self):
        with patch("codecarbon.core.telemetry.client.requests.post") as mock_post:
            mock_post.side_effect = ConnectionError("network down")
            with patch("codecarbon.core.telemetry.client.logger"):
                result = post_private(_settings(), TELEMETRY)
        self.assertFalse(result)

    def test_post_private_skips_when_deadline_passed(self):
        with patch("codecarbon.core.telemetry.client.requests.post") as mock_post:
            result = post_private(_settings(), TELEMETRY, deadline=time.monotonic() - 1)
        self.assertFalse(result)
        mock_post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
