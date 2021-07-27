from typing import List

from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import Organization, OrganizationCreate
from carbonserver.api.services.organization_service import OrganizationService

ORGANIZATIONS_ROUTER_TAGS = ["Organizations"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.post(
    "/organization",
    tags=ORGANIZATIONS_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
    response_model=Organization,
)
@inject
def add_organization(
    organization: OrganizationCreate,
    organization_service: OrganizationService = Depends(
        Provide[ServerContainer.organization_service]
    ),
) -> Organization:
    return organization_service.add_organization(organization)


@router.get(
    "/organization/{organization_id}",
    tags=ORGANIZATIONS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=Organization,
)
@inject
def read_organization(
    organization_id: str,
    organization_service: OrganizationService = Depends(
        Provide[ServerContainer.organization_service]
    ),
) -> Organization:
    return organization_service.read_organization(organization_id)


@router.get(
    "/organizations",
    tags=ORGANIZATIONS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=List[Organization],
)
@inject
def list_organizations(
    organization_service: OrganizationService = Depends(
        Provide[ServerContainer.organization_service]
    ),
) -> List[Organization]:
    return organization_service.list_organizations()
