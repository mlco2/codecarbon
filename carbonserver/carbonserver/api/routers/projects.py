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

PROJECTS_ROUTER_TAGS = ["Projects"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


projects_temp_db = []


@router.post(
    "/projects",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
    response_model=Project,
)
@inject
def add_project(
    project: ProjectCreate,
    project_service=Depends(Provide[ServerContainer.project_service]),
) -> Project:
    return project_service.add_project(project)


# Delete project
@router.delete(
    "/projects/{project_id}",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
def delete_project(
    project_id: str, project_service=Depends(Provide[ServerContainer.project_service])
) -> None:
    return project_service.delete_project(project_id)


# Patch project
@router.patch(
    "/projects/{project_id}",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=Project,
)
@inject
def patch_project(
    project_id: str,
    project: ProjectPatch,
    project_service=Depends(Provide[ServerContainer.project_service]),
) -> Project:
    return project_service.patch_project(project_id, project)


@router.get("/projects/{project_id}", tags=PROJECTS_ROUTER_TAGS, response_model=Project)
@inject
def read_project(
    project_id: str, project_service=Depends(Provide[ServerContainer.project_service])
) -> Project:
    return project_service.get_one_project(project_id)


@router.get(
    "/projects/{project_id}/sums",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_project_detailed_sums(
    project_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
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


@router.get(
    "/organizations/{organization_id}/projects",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def list_projects_nested(
    organization_id: str,
    project_service: ProjectService = Depends(Provide[ServerContainer.project_service]),
) -> List[Project]:
    return project_service.list_projects_from_organization(organization_id)


@router.get(
    "/projects",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def list_projects(
    organization: str,
    project_service: ProjectService = Depends(Provide[ServerContainer.project_service]),
) -> List[Project]:
    return project_service.list_projects_from_organization(organization)
