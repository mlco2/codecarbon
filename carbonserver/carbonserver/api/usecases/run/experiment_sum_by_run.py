from typing import List

from carbonserver.api.errors import NotAllowedError, NotAllowedErrorEnum, UserException
from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository
from carbonserver.api.schemas import RunReport
from carbonserver.api.services.auth_context import AuthContext


class ExperimentSumsByRunUsecase:
    def __init__(
        self, run_repository: SqlAlchemyRepository, auth_context: AuthContext
    ) -> None:
        self._run_repository = run_repository
        self._auth_context = auth_context

    def compute_detailed_sum(
        self, experiment_id: str, start_date, end_date, user=None
    ) -> List[RunReport]:
        if not self._auth_context.can_read_experiment(experiment_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
                    message="Operation not authorized",
                )
            )
        sums = self._run_repository.get_experiment_detailed_sums_by_run(
            experiment_id,
            start_date,
            end_date,
        )
        return sums
