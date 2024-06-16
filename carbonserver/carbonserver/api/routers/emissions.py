from typing import Generic, TypeVar
from uuid import UUID

from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from fastapi_pagination import Page, paginate
from fastapi_pagination.default import Page as BasePage
from fastapi_pagination.default import Params as BaseParams
from starlette import status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import Emission, EmissionCreate
from carbonserver.api.services.emissions_service import EmissionService

# T, Params and Page are needed to override default pagination of get_emissions_from_run
T = TypeVar("T")


class Params(BaseParams):
    # Default results to 100 to avoid crash in /docs
    size: int = Query(100, ge=1, le=10_000, description="Page size")


class Page(BasePage[T], Generic[T]):  # noqa: F811
    __params_type__ = Params


EMISSIONS_ROUTER_TAGS = ["Emissions"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.post(
    "/emissions",
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
    "/emissions/{emission_id}",
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
    "/emissions/run/{run_id}", tags=EMISSIONS_ROUTER_TAGS, response_model=Page[Emission]
)
@inject
def get_emissions_from_run(
    run_id: str,
    emission_service: EmissionService = Depends(
        Provide[ServerContainer.emission_service]
    ),
    params: Params = Depends(),
) -> Page[Emission]:
    return paginate(emission_service.get_emissions_from_run(run_id), params)
