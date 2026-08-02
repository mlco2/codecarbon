"""Service layer for handling telemetry data in the CarbonServer API."""

from uuid import UUID

from carbonserver.api.infra.repositories.repository_telemetry import (
    SqlAlchemyRepository as TelemetrySqlRepository,
)
from carbonserver.api.schemas_telemetry import TelemetryCreate


class TelemetryService:
    def __init__(self, telemetry_repository: TelemetrySqlRepository):
        self._repository = telemetry_repository

    def add_telemetry(self, telemetry: TelemetryCreate) -> UUID:
        return self._repository.add_telemetry(telemetry)
