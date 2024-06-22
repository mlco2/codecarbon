from datetime import datetime, timedelta
from typing import List, Optional

import dateutil.relativedelta
from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import (
    Organization,
    OrganizationCreate,
    OrganizationReport,
)
from carbonserver.api.services.organization_service import OrganizationService
from carbonserver.api.usecases.organization.organization_sum import (
    OrganizationSumsUsecase,
)

ORGANIZATIONS_ROUTER_TAGS = ["Organizations"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.post(
    "/organizations",
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
    "/organizations/{organization_id}",
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


@router.get(
    "/organizations/{organization_id}/sums",
    tags=ORGANIZATIONS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_organization_detailed_sums(
    organization_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    organization_global_sum_usecase: OrganizationSumsUsecase = Depends(
        Provide[ServerContainer.organization_sums_usecase]
    ),
) -> OrganizationReport:
    start_date = (
        start_date
        if start_date
        else datetime.now() - dateutil.relativedelta.relativedelta(months=3)
    )
    end_date = end_date if end_date else datetime.now() + timedelta(days=1)
    return organization_global_sum_usecase.compute_detailed_sum(
        organization_id, start_date, end_date
    )
