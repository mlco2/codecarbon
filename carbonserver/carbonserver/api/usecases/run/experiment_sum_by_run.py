from typing import List

from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository
from carbonserver.api.schemas import RunReport


class ExperimentSumsByRunUsecase:
    def __init__(self, run_repository: SqlAlchemyRepository) -> None:
        self._run_repository = run_repository

    def compute_detailed_sum(
        self, experiment_id: str, start_date, end_date
    ) -> List[RunReport]:
        sums = self._run_repository.get_experiment_detailed_sums_by_run(
            experiment_id,
            start_date,
            end_date,
        )
        return sums
