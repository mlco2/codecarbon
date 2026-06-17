import unittest
from unittest.mock import patch

import requests_mock
from pydantic import ValidationError

from codecarbon.core.telemetry import (
    TelemetrySettings,
    post_private,
    post_public_summary,
)
from codecarbon.output_methods.emissions_data import EmissionsData


class TestPostPrivate(unittest.TestCase):
    def _settings(self, api_url: str = "http://test.com", api_key: str | None = None):
        return TelemetrySettings(
            level=TelemetrySettings.resolve().level,
            source="default",
            api_url=api_url,
            api_key=api_key or TelemetrySettings.resolve().api_key,
            experiment_id=TelemetrySettings.resolve().experiment_id,
        )

    def test_post_private_sends_validated_payload(self):
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
            result = post_private(self._settings(), telemetry)

            self.assertTrue(result)
            self.assertEqual(m.call_count, 1)
            self.assertEqual(
                m.last_request.json(),
                {
                    **telemetry,
                    "timestamp": "2026-05-03T12:00:00Z",
                },
            )

    def test_post_private_rejects_invalid_payload(self):
        with self.assertRaises(ValidationError):
            post_private(
                self._settings(),
                {
                    "timestamp": "2026-05-03T12:00:00+00:00",
                    "telemetry_level": "minimal",
                    "unknown_field": "value",
                },
            )

    def test_post_private_logs_warning_on_404(self):
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
            with patch("codecarbon.core.telemetry.client.logger") as mock_logger:
                result = post_private(self._settings(), telemetry)
        self.assertFalse(result)
        mock_logger.warning.assert_called_once()

    def test_post_private_sends_api_key_header_when_configured(self):
        telemetry = {
            "timestamp": "2026-05-03T12:00:00+00:00",
            "telemetry_level": "minimal",
        }
        settings = TelemetrySettings(
            level=TelemetrySettings.resolve().level,
            source="default",
            api_url="http://test.com",
            api_key="cpt_test_key",
            experiment_id=TelemetrySettings.resolve().experiment_id,
        )
        with requests_mock.Mocker() as m:
            m.post(
                "http://test.com/telemetry",
                json="telemetry-id",
                status_code=201,
            )
            post_private(settings, telemetry)
        self.assertEqual(m.last_request.headers["x-api-token"], "cpt_test_key")

    def test_post_private_returns_false_on_request_error(self):
        telemetry = {
            "timestamp": "2026-05-03T12:00:00+00:00",
            "telemetry_level": "minimal",
        }
        with patch("codecarbon.core.telemetry.client.requests.post") as mock_post:
            mock_post.side_effect = ConnectionError("network down")
            with patch("codecarbon.core.telemetry.client.logger"):
                result = post_private(self._settings(), telemetry)
        self.assertFalse(result)


class TestPostPublicSummary(unittest.TestCase):
    def _settings(self) -> TelemetrySettings:
        return TelemetrySettings(
            level=TelemetrySettings.resolve().level,
            source="default",
            api_url="http://test.com",
            api_key="cpt_test_key",
            experiment_id="00000000-0000-0000-0000-000000000001",
        )

    def _emissions(self) -> EmissionsData:
        return EmissionsData(
            timestamp="2026-05-03T12:00:00+00:00",
            project_name="p",
            run_id="r",
            experiment_id="e",
            duration=10.0,
            emissions=0.001,
            emissions_rate=0.0001,
            cpu_power=0.0,
            gpu_power=0.0,
            ram_power=0.0,
            cpu_energy=0.0,
            gpu_energy=0.0,
            ram_energy=0.0,
            energy_consumed=0.01,
            water_consumed=0.0,
            country_name="France",
            country_iso_code="FRA",
            region="idf",
            cloud_provider="",
            cloud_region="",
            os="Linux",
            python_version="3.11",
            codecarbon_version="2.0",
            cpu_count=1.0,
            cpu_model="cpu",
            gpu_count=0.0,
            gpu_model="",
            longitude=0.0,
            latitude=0.0,
            ram_total_size=8.0,
            tracking_mode="machine",
        )

    def test_post_public_summary_returns_true_on_success(self):
        with patch("codecarbon.core.telemetry.client.ApiClient") as mock_client:
            mock_client.return_value.add_emission.return_value = True
            result = post_public_summary(self._settings(), {}, self._emissions())
        self.assertTrue(result)

    def test_post_public_summary_returns_false_on_error(self):
        with patch(
            "codecarbon.core.telemetry.client.ApiClient",
            side_effect=RuntimeError("api down"),
        ):
            with patch("codecarbon.core.telemetry.client.logger") as mock_logger:
                result = post_public_summary(self._settings(), {}, self._emissions())
        self.assertFalse(result)
        mock_logger.error.assert_called_once()


class TestPostPrivateErrors(unittest.TestCase):
    def test_post_private_logs_error_on_unexpected_status(self):
        telemetry = {
            "timestamp": "2026-05-03T12:00:00+00:00",
            "telemetry_level": "minimal",
        }
        settings = TelemetrySettings(
            level=TelemetrySettings.resolve().level,
            source="default",
            api_url="http://test.com",
            api_key="cpt_test_key",
            experiment_id=TelemetrySettings.resolve().experiment_id,
        )
        with requests_mock.Mocker() as m:
            m.post("http://test.com/telemetry", text="server error", status_code=500)
            with patch("codecarbon.core.telemetry.client.logger") as mock_logger:
                result = post_private(settings, telemetry)
        self.assertFalse(result)
        mock_logger.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
