from datetime import datetime, timedelta
from typing import List, Optional

import dateutil.relativedelta
from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import Project, ProjectCreate, ProjectPatch, ProjectReport
from carbonserver.api.services.project_service import ProjectService
from carbonserver.api.usecases.project.project_sum import ProjectSumsUsecase
from carbonserver.api.services.auth_service import UserWithAuthDependency

PROJECTS_ROUTER_TAGS = ["Projects"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.post(
    "/projects",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
    response_model=Project,
)
@inject
def add_project(
    project: ProjectCreate,
    auth_user: UserWithAuthDependency = Depends(UserWithAuthDependency),
    project_service=Depends(Provide[ServerContainer.project_service]),
) -> Project:
    if project.organization_id not in auth_user.db_user.organizations:
        raise UserException(
            NotAllowedError(
                code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
                message="Cannot add project to organization",
            )
        )
    else:
        return project_service.add_project(project, auth_user.db_user)


# Delete project
@router.delete(
    "/projects/{project_id}",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
def delete_project(
    organization_id: str,
    project_id: str,
    auth_user: UserWithAuthDependency = Depends(UserWithAuthDependency),
    project_service=Depends(Provide[ServerContainer.project_service]),
) -> None:
    if organization_id not in auth_user.db_user.organizations:
        raise UserException(
            NotAllowedError(
                code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
                message="Cannot delete project from organization",
            )
        )
    else:
        return project_service.delete_project(project_id, auth_user.db_user)


# Patch project
@router.patch(
    "/projects/{project_id}",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=Project,
)
@inject
def patch_project(
    project: ProjectPatch,
    auth_user: UserWithAuthDependency = Depends(UserWithAuthDependency),
    project_service=Depends(Provide[ServerContainer.project_service]),
) -> Project:
    return project_service.patch_project(project, auth_user.db_user)


@router.get(
    "/projects/{project_id}",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=Project
)
@inject
def read_project(
    project_id: str,
    auth_user: UserWithAuthDependency = Depends(UserWithAuthDependency),
    project_service=Depends(Provide[ServerContainer.project_service]),
) -> Project:
    return project_service.get_one_project(project_id, auth_user.db_user)


@router.get(
    "/organizations/{organization_id}/projects",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=List[Project]
)
@inject
def list_projects_nested(
    organization_id: str,
    auth_user: UserWithAuthDependency = Depends(UserWithAuthDependency),
    project_service: ProjectService = Depends(Provide[ServerContainer.project_service]),
) -> List[Project]:
    if organization_id not in auth_user.db_user.organizations:
        raise UserException(
            NotAllowedError(
                code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
                message="Cannot read project from organization",
            )
        )
    else:
        return project_service.list_projects_from_organization(organization_id, auth_user.db_user)


@router.get(
    "/projects",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=List[Project]
)
@inject
def list_projects(
    organization_id: str,
    auth_user: UserWithAuthDependency = Depends(UserWithAuthDependency),
    project_service: ProjectService = Depends(Provide[ServerContainer.project_service]),
) -> List[Project]:
    return project_service.list_projects_from_organization(organization_id, auth_user.db_user)


@router.get(
    "/projects/{project_id}/sums",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=ProjectReport
)
@inject
def read_project_detailed_sums(
    project_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    auth_user: UserWithAuthDependency = Depends(UserWithAuthDependency),
    project_global_sum_usecase: ProjectSumsUsecase = Depends(
        Provide[ServerContainer.project_sums_usecase]
    ),
) -> ProjectReport:
    start_date = (
        start_date
        if start_date
        else datetime.now() - dateutil.relativedelta.relativedelta(months=3)
    )
    end_date = end_date if end_date else datetime.now() + timedelta(days=1)
    return project_global_sum_usecase.compute_detailed_sum(
        project_id, start_date, end_date
    )
