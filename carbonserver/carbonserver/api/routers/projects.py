from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import ProjectCreate

PROJECTS_ROUTER_TAGS = ["Projects"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


projects_temp_db = []


@router.put("/project", tags=PROJECTS_ROUTER_TAGS, status_code=status.HTTP_201_CREATED)
@inject
def add_project(
    project: ProjectCreate,
    project_service=Depends(Provide[ServerContainer.project_service]),
):
    return project_service.add_project(project)


@router.get("/project/{project_id}", tags=PROJECTS_ROUTER_TAGS)
@inject
def read_project(
    project_id: str, project_service=Depends(Provide[ServerContainer.project_service])
):
    return project_service.get_one_project(project_id)
