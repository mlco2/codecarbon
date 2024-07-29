from uuid import UUID

from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository as ProjectRepository,
)

from carbonserver.api.infra.repositories.users.sql_repository import (
    SqlAlchemyRepository as UserRepository,
)

from carbonserver.api.schemas import ProjectCreate

from carbonserver.api.errors import UserException, NotAllowedError, NotAllowedErrorEnum
from carbonserver.api.schemas import User, ProjectPatch


class ProjectService:
    def __init__(self,
                 project_repository: ProjectRepository,
                 user_repository: UserRepository,
                 ):
        self._project_repository = project_repository
        self._user_repository = user_repository

    def add_project(self, project: ProjectCreate):
        if self.isOperationAuthorized(project.organization_id, project.user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot add experiment to project from this organization.",
                )
            )
        return self._project_repository.add_project(project)

    def delete_project(self, project_id: UUID, user):
        if not self.isOperationAuthorizedOnProject(project_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot add experiment to project from this organization.",
                )
            )
        return self._project_repository.delete_project(project_id)

    def patch_project(self, project_id: UUID, project: ProjectPatch):
        if not self.isOperationAuthorizedOnProject(project_id, project.user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot add experiment to project from this organization.",
                )
            )
        return self._project_repository.patch_project(project_id, project)

    def get_one_project(self, project_id: UUID, user: User):
        project = self._project_repository.get_one_project(project_id)
        if not self.isOperationAuthorized(project.organization_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot add experiment to project from this organization.",
                )
            )
        return project

    def list_projects_from_organization(self, organization_id: UUID, user: User):
        if not self.isOperationAuthorized(organization_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot add experiment to project from this organization.",
                )
            )
        return self._project_repository.get_projects_from_organization(organization_id)

    def isOperationAuthorized(self, organization_id, user: User):
        db_user = self._user_repository.get_user_by_id(user.id)
        return organization_id in db_user.organizations

    def isOperationAuthorizedOnProject(self, project_id, user):
        return self._user_repository.is_user_authorized_on_project(project_id, user.id)
