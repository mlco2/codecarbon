import logging
from uuid import UUID

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository as OrganizationRepository,
)
from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository as ProjectRepository,
)
from carbonserver.api.infra.repositories.repository_users import (
    SqlAlchemyRepository as UserRepository,
)
from carbonserver.api.schemas import OrganizationCreate, ProjectCreate, User, UserCreate

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
        self._default_org_id = UUID("e52fe339-164d-4c2b-a8c0-f562dfce066d")
        self._default_api_key = "default"

    def sign_up(
        self,
        user: UserCreate,
    ) -> User:
        created_user = self._user_repository.create_user(user)
        subscribed_user = self.new_user_setup(created_user)
        LOGGER.info(f"User {subscribed_user.id} created")
        return subscribed_user

    def subscribe_user_to_org(
        self, user: User, organization_id: UUID, organization_api_key: str
    ):
        key_is_valid = self._organization_repository.is_api_key_valid(
            organization_id, organization_api_key
        )
        if key_is_valid:
            user = self._user_repository.subscribe_user_to_org(user, organization_id)
        return user

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
        subscribed_user = self.subscribe_user_to_org(
            user, organization_created.id, self._default_api_key
        )
        return subscribed_user
