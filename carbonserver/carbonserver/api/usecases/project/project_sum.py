from carbonserver.api.errors import NotAllowedError, NotAllowedErrorEnum, UserException
from carbonserver.api.infra.repositories.repository_projects import SqlAlchemyRepository
from carbonserver.api.schemas import ProjectReport
from carbonserver.api.services.auth_context import AuthContext


class ProjectSumsUsecase:
    def __init__(
        self, project_repository: SqlAlchemyRepository, auth_context: AuthContext
    ) -> None:
        self._project_repository = project_repository
        self._auth_context = auth_context

    def compute_detailed_sum(
        self, project_id: str, start_date, end_date, user=None
    ) -> ProjectReport:
        if not self._auth_context.can_read_project(project_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
                    message="Operation not authorized",
                )
            )
        sums = self._project_repository.get_project_detailed_sums(
            project_id,
            start_date,
            end_date,
        )
        return sums
