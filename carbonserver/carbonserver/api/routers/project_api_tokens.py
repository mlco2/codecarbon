from typing import List

from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import ProjectToken, ProjectTokenCreate
from carbonserver.api.services.auth_service import (
    MandatoryUserWithAuthDependency,
    UserWithAuthDependency,
)
from carbonserver.api.services.project_token_service import ProjectTokenService

PROJECTS_TOKENS_ROUTER_TAGS = ["Project tokens"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)
# TODO: Add authentication to the endpoints


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
    auth_user: UserWithAuthDependency = Depends(MandatoryUserWithAuthDependency),
    project_token_service: ProjectTokenService = Depends(
        Provide[ServerContainer.project_token_service]
    ),
) -> ProjectToken:
    return project_token_service.add_project_token(
        project_id, project_token, user=auth_user.db_user
    )


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
    auth_user: UserWithAuthDependency = Depends(MandatoryUserWithAuthDependency),
    project_token_service: ProjectTokenService = Depends(
        Provide[ServerContainer.project_token_service]
    ),
) -> None:
    return project_token_service.delete_project_token(
        project_id, token_id, user=auth_user.db_user
    )


# See all project tokens of the project
@router.get(
    "/projects/{project_id}/api-tokens",
    tags=PROJECTS_TOKENS_ROUTER_TAGS,
    response_model=List[ProjectToken],
)
@inject
def get_all_project_tokens(
    project_id: str,
    auth_user: UserWithAuthDependency = Depends(MandatoryUserWithAuthDependency),
    project_token_service: ProjectTokenService = Depends(
        Provide[ServerContainer.project_token_service]
    ),
) -> List[ProjectToken]:
    return project_token_service.list_tokens_from_project(
        project_id, user=auth_user.db_user
    )
