from typing import List

from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import OrganizationCreate, ProjectCreate, User, UserCreate
from carbonserver.api.services.organization_service import OrganizationService
from carbonserver.api.services.project_service import ProjectService
from carbonserver.api.services.signup_service import SignUpService
from carbonserver.api.services.user_service import UserService

USERS_ROUTER_TAGS = ["Users"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.post(
    "/users",
    tags=USERS_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
    response_model=User,
)
@inject
def create_user(
    user: UserCreate,
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
    organization_service: OrganizationService = Depends(
        Provide[ServerContainer.organization_service]
    ),
    project_service: ProjectService = Depends(Provide[ServerContainer.project_service]),
) -> User:
    user_created = user_service.create_user(user)
    if user_created is None:
        return user_created

    new_user_steps(user_created, organization_service, project_service)
    return user_created


@router.post(
    "/users/signup",
    tags=USERS_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
    response_model=User,
)
@inject
def sign_up(
    user: UserCreate,
    signup_service: SignUpService = Depends(Provide[ServerContainer.sign_up_service]),
) -> User:
    return signup_service.sign_up(user)


@router.get(
    "/users",
    tags=USERS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=List[User],
)
@inject
def list_users(
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
) -> List[User]:
    return user_service.list_users()


@router.get(
    "/users/{user_id}",
    tags=USERS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=User,
)
@inject
def get_user_by_id(
    user_id: str,
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
) -> User:
    return user_service.get_user_by_id(user_id)


def new_user_steps(
    user: User,
    organization_service: OrganizationService,
    project_service: ProjectService,
):
    """
    Steps to be run for every new user created
    """
    # TODO: Add a transaction to rollback if any of the following steps fail
    # Create an organization for the user
    organization = OrganizationCreate(
        name=user.name, description="Default organization"
    )
    organization_created = organization_service.add_organization(organization)
    # Create a project for the user
    project = ProjectCreate(
        name=user.name,
        description="Default project",
        organization_id=organization_created.id,
    )
    project_service.add_project(project)
    # TODO: Add default flag to the generated project and organization and do not allow to delete them
