import abc
from uuid import UUID

from carbonserver.api import schemas_telemetry


class Telemetry(abc.ABC):
    @abc.abstractmethod
    def add_telemetry(self, telemetry: schemas_telemetry.TelemetryCreate) -> UUID:
        raise NotImplementedError
