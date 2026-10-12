import unittest

import requests_mock
from pydantic import ValidationError

from codecarbon.core.telemetry_client import TelemetryClient
from codecarbon.core.telemetry_schemas import TelemetryCreate


class TestTelemetryClient(unittest.TestCase):
    def test_init_sets_up_client_without_calling_api(self):
        with requests_mock.Mocker() as m:
            client = TelemetryClient(
                endpoint_url="http://test.com/",
                telemetry={
                    "timestamp": "2026-05-03T12:00:00+00:00",
                    "telemetry_level": "minimal",
                },
            )

            self.assertEqual(client.endpoint_url, "http://test.com")
            self.assertEqual(client.telemetry_url, "http://test.com/telemetry")
            self.assertIsInstance(client.telemetry, TelemetryCreate)
            self.assertEqual(m.call_count, 0)

    def test_add_telemetry_posts_configured_payload(self):
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
            client = TelemetryClient(
                endpoint_url="http://test.com", telemetry=telemetry
            )

            actual_telemetry_id = client.add_telemetry()

            self.assertEqual(
                actual_telemetry_id, "f52fe339-164d-4c2b-a8c0-f562dfce066d"
            )
            self.assertEqual(m.call_count, 1)
            self.assertEqual(
                m.last_request.json(),
                {
                    **telemetry,
                    "timestamp": "2026-05-03T12:00:00Z",
                },
            )

    def test_add_telemetry_posts_call_payload(self):
        telemetry = TelemetryCreate(
            timestamp="2026-05-03T12:00:00+00:00",
            telemetry_level="minimal",
            os="Linux-5.10.0-x86_64",
        )

        with requests_mock.Mocker() as m:
            m.post(
                "http://test.com/telemetry",
                json="f52fe339-164d-4c2b-a8c0-f562dfce066d",
                status_code=201,
            )
            client = TelemetryClient(endpoint_url="http://test.com")

            actual_telemetry_id = client.add_telemetry(telemetry)

            self.assertEqual(
                actual_telemetry_id, "f52fe339-164d-4c2b-a8c0-f562dfce066d"
            )
            self.assertEqual(m.call_count, 1)
            self.assertEqual(
                m.last_request.json(),
                {
                    "timestamp": "2026-05-03T12:00:00Z",
                    "telemetry_level": "minimal",
                    "os": "Linux-5.10.0-x86_64",
                },
            )

    def test_init_rejects_invalid_telemetry_without_calling_api(self):
        with requests_mock.Mocker() as m:
            with self.assertRaises(ValidationError):
                TelemetryClient(
                    endpoint_url="http://test.com",
                    telemetry={
                        "timestamp": "2026-05-03T12:00:00+00:00",
                        "telemetry_level": "minimal",
                        "total_emissions_kg": 0.42,
                    },
                )

            self.assertEqual(m.call_count, 0)

    def test_add_telemetry_returns_none_without_payload(self):
        client = TelemetryClient(endpoint_url="http://test.com")

        self.assertIsNone(client.add_telemetry())
