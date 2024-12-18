from typing import List

from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.schemas import ProjectToken, ProjectTokenCreate

PROJECTS_TOKENS_ROUTER_TAGS = ["Project tokens"]

router = APIRouter()


# Create project token
@router.post(
    "/projects/{project_id}/api-tokens",
    tags=PROJECTS_TOKENS_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectToken,
)
@inject
def add_project_token(
    project_id: str,
    project_token: ProjectTokenCreate,
    project_token_service=Depends(Provide[ServerContainer.project_token_service]),
) -> ProjectToken:
    return project_token_service.add_project_token(project_id, project_token)


# Delete project token
@router.delete(
    "/projects/{project_id}/api-tokens/{token_id}",
    tags=PROJECTS_TOKENS_ROUTER_TAGS,
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
def delete_project_token(
    project_id: str,
    token_id: str,
    project_token_service=Depends(Provide[ServerContainer.project_token_service]),
) -> None:
    return project_token_service.delete_project_token(project_id, token_id)


# See all project tokens of the project
@router.get(
    "/projects/{project_id}/api-tokens",
    tags=PROJECTS_TOKENS_ROUTER_TAGS,
    response_model=List[ProjectToken],
)
@inject
def get_all_project_tokens(
    project_id: str,
    project_token_service=Depends(Provide[ServerContainer.project_token_service]),
) -> List[ProjectToken]:
    return project_token_service.list_tokens_from_project(project_id)
