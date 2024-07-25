from typing import Generic, TypeVar, Optional
from uuid import UUID

from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from fastapi_pagination import Page, paginate
from fastapi_pagination.default import Page as BasePage
from fastapi_pagination.default import Params as BaseParams
from fief_client import FiefUserInfo
from starlette import status

from carbonserver.api.schemas import Emission, EmissionCreate
from carbonserver.api.services.emissions_service import EmissionService

from carbonserver.carbonserver.api.routers.authenticate import fief_auth

# T, Params and Page are needed to override default pagination of get_emissions_from_run
T = TypeVar("T")


class Params(BaseParams):
    # Default results to 100 to avoid crash in /docs
    size: int = Query(100, ge=1, le=10_000, description="Page size")


class Page(BasePage[T], Generic[T]):  # noqa: F811
    __params_type__ = Params


EMISSIONS_ROUTER_TAGS = ["Emissions"]

router = APIRouter()


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
    "/runs/{run_id}/emissions",
    tags=EMISSIONS_ROUTER_TAGS,
    response_model=Page[Emission],
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


@router.get("/emissions", tags=EMISSIONS_ROUTER_TAGS, response_model=Page[Emission])
@inject
def get_emissions(
    run_id: str,
    emission_service: EmissionService = Depends(
        Provide[ServerContainer.emission_service]
    ),
    params: Params = Depends(),
) -> Page[Emission]:
    return paginate(emission_service.get_emissions_from_run(run_id), params)
