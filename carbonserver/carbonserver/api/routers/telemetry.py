"""API router for handling telemetry data in the CarbonServer API."""

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header
from starlette import status

from carbonserver.api.schemas import AccessLevel
from carbonserver.api.schemas_telemetry import TelemetryCreate
from carbonserver.api.services.project_token_service import ProjectTokenService
from carbonserver.api.services.telemetry_service import TelemetryService
from carbonserver.config import settings
from carbonserver.container import ServerContainer

TELEMETRY_ROUTER_TAGS = ["Telemetry"]

router = APIRouter()


@router.post(
    "/telemetry",
    tags=TELEMETRY_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
    response_model=UUID,
)
@inject
def add_telemetry(
    telemetry: TelemetryCreate,
    telemetry_service: TelemetryService = Depends(
        Provide[ServerContainer.telemetry_service]
    ),
    project_token_service: ProjectTokenService = Depends(
        Provide[ServerContainer.project_token_service]
    ),
    x_api_token: str = Header(None),
) -> UUID:
    project_token_service.project_token_has_access(
        AccessLevel.WRITE.value,
        experiment_id=settings.telemetry_experiment_id,
        project_token=x_api_token,
    )
    return telemetry_service.add_telemetry(telemetry)
