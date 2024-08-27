from carbonserver.api.errors import NotAllowedError, NotAllowedErrorEnum, UserException
from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository as ProjectSqlRepository,
)
from carbonserver.api.schemas import ProjectCreate, ProjectPatch, User
from carbonserver.api.services.auth_context import AuthContext


class ProjectService:
    def __init__(
        self, auth_context: AuthContext, project_repository: ProjectSqlRepository
    ):
        self._auth_context = auth_context
        self._repository = project_repository

    def add_project(self, project: ProjectCreate, user: User):
        if not self._auth_context.isOperationAuthorizedOnOrg(
            project.organization_id, user
        ):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot add project to this organization.",
                )
            )
        else:
            return self._repository.add_project(project)

    def delete_project(self, project_id, user):
        if not self._auth_context.isOperationAuthorizedOnProject(project_id, user=user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot remove project from this organization.",
                )
            )
        else:
            return self._repository.delete_project(project_id)

    def patch_project(self, project_id, project: ProjectPatch, user: User):
        if not self._auth_context.isOperationAuthorizedOnProject(project_id, user=user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot update project from this organization.",
                )
            )
        else:
            return self._repository.patch_project(project_id, project)

    def get_one_project(self, project_id: str, user: User):
        if not self._auth_context.isOperationAuthorizedOnProject(project_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot read project from this organization.",
                )
            )
        else:
            return self._repository.get_one_project(project_id)

    def list_projects_from_organization(self, organization_id: str, user: User):
        if not self._auth_context.isOperationAuthorizedOnOrg(organization_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot read projects to this organization.",
                )
            )
        else:
            return self._repository.get_projects_from_organization(organization_id)
