from typing import List

from carbonserver.api.errors import NotAllowedError, NotAllowedErrorEnum, UserException
from carbonserver.api.infra.repositories.repository_experiments import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import ExperimentReport
from carbonserver.api.services.auth_context import AuthContext


class ProjectSumsByExperimentUsecase:
    def __init__(
        self, experiment_repository: SqlAlchemyRepository, auth_context: AuthContext
    ) -> None:
        self._experiment_repository = experiment_repository
        self._auth_context = auth_context

    def compute_detailed_sum(
        self, project_id: str, start_date, end_date, user=None
    ) -> List[ExperimentReport]:
        if not self._auth_context.can_read_project(project_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
                    message="Operation not authorized",
                )
            )
        return self._experiment_repository.get_project_detailed_sums_by_experiment(
            project_id,
            start_date,
            end_date,
        )
