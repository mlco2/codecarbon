"""API router for handling telemetry data in the CarbonServer API."""

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.schemas_telemetry import TelemetryCreate
from carbonserver.api.services.telemetry_service import TelemetryService
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
) -> UUID:
    return telemetry_service.add_telemetry(telemetry)
