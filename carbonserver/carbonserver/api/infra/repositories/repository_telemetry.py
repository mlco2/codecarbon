"""Repository implementation for telemetry data using SQLAlchemy."""

import uuid
from contextlib import AbstractContextManager
from uuid import UUID

from dependency_injector.providers import Callable

from carbonserver.api.domain.telemetry import Telemetry
from carbonserver.api.infra.database.telemetry_sql_models import (
    Telemetry as SqlModelTelemetry,
)
from carbonserver.api.schemas_telemetry import TelemetryCreate


class SqlAlchemyRepository(Telemetry):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def add_telemetry(self, telemetry: TelemetryCreate) -> UUID:
        with self.session_factory() as session:
            db_telemetry = SqlModelTelemetry(
                id=uuid.uuid4(),
                **telemetry.model_dump(),
            )
            session.add(db_telemetry)
            session.commit()
            return db_telemetry.id
