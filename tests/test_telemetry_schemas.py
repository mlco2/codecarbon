import unittest
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from codecarbon.core.telemetry.schemas import TelemetryCreate, TelemetryLevel


class TestTelemetrySchemaValidation(unittest.TestCase):
    def _minimal_payload(self) -> dict:
        return {
            "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "telemetry_level": TelemetryLevel.minimal,
            "os": "Linux",
        }

    def test_rejects_disabled_telemetry_level(self):
        with pytest.raises(
            ValidationError, match="Disabled telemetry must not be submitted"
        ):
            TelemetryCreate(
                **{**self._minimal_payload(), "telemetry_level": "disabled"}
            )

    def test_rejects_minimal_with_extensive_field(self):
        with pytest.raises(
            ValidationError, match="Minimal telemetry cannot include extensive fields"
        ):
            TelemetryCreate(
                **{
                    **self._minimal_payload(),
                    "total_emissions_kg": 0.5,
                }
            )


if __name__ == "__main__":
    unittest.main()
