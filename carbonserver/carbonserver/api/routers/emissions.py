from typing import List
from uuid import UUID

from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import Emission, EmissionCreate
from carbonserver.api.services.emissions_service import EmissionService

EMISSIONS_ROUTER_TAGS = ["Emissions"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.post(
    "/emission",
    tags=EMISSIONS_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
    response_model=UUID,
)
@inject
def add_emission(
    emission: EmissionCreate,
    emission_service: EmissionService = Depends(
        Provide[ServerContainer.emission_service]
    ),
) -> UUID:
    return emission_service.add_emission(emission)


@router.get(
    "/emission/{emission_id}",
    tags=EMISSIONS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=Emission,
)
@inject
def read_emission(
    emission_id: str,
    emission_service: EmissionService = Depends(
        Provide[ServerContainer.emission_service]
    ),
) -> Emission:
    return emission_service.get_one_emission(emission_id)


@router.get(
    "/emissions/run/{run_id}", tags=EMISSIONS_ROUTER_TAGS, response_model=List[Emission]
)
@inject
def get_emissions_from_run(
    run_id: str,
    emission_service: EmissionService = Depends(
        Provide[ServerContainer.emission_service]
    ),
) -> List[Emission]:
    return emission_service.get_emissions_from_run(run_id)
