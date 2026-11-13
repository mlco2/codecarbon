import re
import unittest
from datetime import datetime, timezone
from pathlib import Path

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

    def test_rejects_unknown_field(self):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            TelemetryCreate(
                **{
                    **self._minimal_payload(),
                    "total_emissions_kg": 0.5,
                }
            )

    def test_rejects_oversized_string(self):
        with pytest.raises(ValidationError, match="at most 256 characters"):
            TelemetryCreate(**{**self._minimal_payload(), "cpu_model": "x" * 257})

    def test_rejects_coordinates(self):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            TelemetryCreate(**{**self._minimal_payload(), "latitude": 48.8})


def test_documented_fields_match_schema():
    """Every field the SDK can send is listed in the user docs, and only those."""
    docs = Path(__file__).parents[1] / "docs" / "how-to" / "telemetry.md"
    section = docs.read_text().split("## Every field sent", 1)[1].split("\n## ", 1)[0]
    documented = {
        name
        for row in section.splitlines()
        if row.startswith("| `")
        for name in re.findall(r"`(\w+)`", row.split("|")[1])
    }
    assert documented == set(TelemetryCreate.model_fields)


if __name__ == "__main__":
    unittest.main()
