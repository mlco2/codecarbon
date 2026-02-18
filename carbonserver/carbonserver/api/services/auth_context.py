from typing import Optional
from uuid import UUID

from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository as ProjectRepository,
)
from carbonserver.api.infra.repositories.repository_projects_tokens import (
    SqlAlchemyRepository as ProjectTokensRepository,
)
from carbonserver.api.infra.repositories.repository_users import (
    SqlAlchemyRepository as UserRepository,
)
from carbonserver.api.schemas import User


class AuthContext:
    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: ProjectTokensRepository,
        project_repository: ProjectRepository,
    ):
        self._user_repository: UserRepository = user_repository
        self._token_repository: ProjectTokensRepository = token_repository
        self._project_repository: ProjectRepository = project_repository

    def isOperationAuthorizedOnOrg(self, organization_id, user: User):
        return self._user_repository.is_user_in_organization(
            organization_id=organization_id, user=user
        )

    def isOperationAuthorizedOnProject(self, project_id: UUID | str, user: User):
        return self._user_repository.is_user_authorized_on_project(project_id, user.id)

    def can_read_project(self, project_id: UUID, user: Optional[User]):
        if self._project_repository.is_project_public(project_id):
            return True
        if user is None:
            raise Exception("Not authenticated")
        return self._user_repository.is_user_authorized_on_project(project_id, user.id)

    def can_read_organization(self, organization_id: UUID, user: User):
        return self._user_repository.is_user_in_organization(
            organization_id=organization_id, user=user
        )

    def can_write_organization(self, organization_id: UUID, user: User):
        return self._user_repository.is_admin_in_organization(
            organization_id=organization_id, user=user
        )

    def can_create_run(self, experiment_id: UUID, user: User):
        return self._user_repository.is_user_authorized_on_experiment(
            experiment_id, user.id
        )
