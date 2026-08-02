from unittest import mock

from carbonserver.api.infra.repositories.repository_telemetry import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas_telemetry import TelemetryCreate
from carbonserver.api.services.telemetry_service import TelemetryService

TELEMETRY_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"


def test_telemetry_service_creates_telemetry():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    telemetry_service = TelemetryService(repository_mock)
    repository_mock.add_telemetry.return_value = TELEMETRY_ID

    telemetry_to_create = TelemetryCreate(
        timestamp="2026-05-03T12:00:00+00:00",
        telemetry_level="minimal",
        os="Linux-5.10.0-x86_64",
        cpu_count=12,
        python_version="3.11.5",
        codecarbon_version="3.2.6",
    )

    actual_saved_telemetry_id = telemetry_service.add_telemetry(telemetry_to_create)

    assert actual_saved_telemetry_id == TELEMETRY_ID
    repository_mock.add_telemetry.assert_called_once_with(telemetry_to_create)
