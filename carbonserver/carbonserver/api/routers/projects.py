from carbonserver.api.services.authentication.authentication_service import auth
from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.schemas import Project, ProjectCreate
from carbonserver.api.services.project_service import ProjectService

PROJECTS_ROUTER_TAGS = ["Projects"]

router = APIRouter(
    dependencies=[Depends(auth)],
)


projects_temp_db = []


@router.post(
    "/project",
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


@router.get("/project/{project_id}", tags=PROJECTS_ROUTER_TAGS, response_model=Project)
@inject
def read_project(
    project_id: str, project_service=Depends(Provide[ServerContainer.project_service])
) -> Project:
    return project_service.get_one_project(project_id)


@router.get(
    "/projects/team/{team_id}",
    tags=PROJECTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_projects_from_team(
    team_id: str,
    project_service: ProjectService = Depends(Provide[ServerContainer.project_service]),
):
    return project_service.list_projects_from_team(team_id)
