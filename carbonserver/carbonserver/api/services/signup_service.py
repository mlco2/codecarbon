import logging
from uuid import UUID

import jwt
import logfire
from fastapi import HTTPException

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository as OrganizationRepository,
)
from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository as ProjectRepository,
)
from carbonserver.api.infra.repositories.repository_users import (
    SqlAlchemyRepository as UserRepository,
)
from carbonserver.api.schemas import (
    OrganizationCreate,
    ProjectCreate,
    User,
    UserAutoCreate,
)

LOGGER = logging.getLogger(__name__)


class SignUpService:
    def __init__(
        self,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
        project_repository: ProjectRepository,
    ) -> None:
        self._user_repository: UserRepository = user_repository
        self._organization_repository: OrganizationRepository = organization_repository
        self._project_repository: ProjectRepository = project_repository

    def sign_up(
        self,
        user: UserAutoCreate,
    ) -> User:
        with logfire.span('User applicative creation'):
            created_user = self._user_repository.create_user(user)
            subscribed_user = self.new_user_setup(created_user)
            logfire.info(subscribed_user)
            LOGGER.info(f"User {subscribed_user.id} created")
        return subscribed_user

    def subscribe_user_to_org(
        self,
        user: User,
        organization_id: UUID,
    ):
        return self._user_repository.subscribe_user_to_org(user, organization_id)

    def new_user_setup(self, user: User) -> User:
        """
        Steps to be run for every new user created
        """

        # TODO: Add a transaction to rollback if any of the following steps fail
        # Create an organization for the user
        organization = OrganizationCreate(
            name=user.name, description="Default organization"
        )
        organization_created = self._organization_repository.add_organization(
            organization
        )
        # Create a project for the user
        project = ProjectCreate(
            name=user.name,
            description="Default project",
            organization_id=organization_created.id,
        )
        self._project_repository.add_project(project)
        # TODO: Add default flag to the generated project and organization and do not allow to delete them
        subscribed_user = self.subscribe_user_to_org(user, organization_created.id)
        return subscribed_user

    def check_jwt_user(self, token: str | dict, create: bool):
        try:
            if isinstance(token, str):
                id_token = jwt.decode(
                    token, options={"verify_signature": False}, algorithms=["HS256"]
                )
            else:
                id_token = token
            self._user_repository.get_user_by_id(id_token["sub"])
        except HTTPException as e:
            if e.status_code == 404:
                if not create:
                    LOGGER.error("Authenticated user not found")
                    raise
                LOGGER.error("Authenticated user not found. Creating.")
                LOGGER.error(f"Id token : {id_token}.")
                name = id_token.get("fields", {}).get("name")

                new_user = UserAutoCreate(
                    id=id_token["sub"],
                    email=id_token["email"],
                    name=name or id_token["email"],
                )
                self.sign_up(new_user)
