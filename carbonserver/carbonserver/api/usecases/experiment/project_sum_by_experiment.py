from typing import List

from carbonserver.api.infra.repositories.repository_experiments import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import ExperimentReport


class ProjectSumsByExperimentUsecase:
    def __init__(self, experiment_repository: SqlAlchemyRepository) -> None:
        self._experiment_repository = experiment_repository

    def compute_detailed_sum(
        self, project_id: str, start_date, end_date, user=None
    ) -> List[ExperimentReport]:
        # TODO: check permissions
        sums = self._experiment_repository.get_project_detailed_sums_by_experiment(
            project_id,
            start_date,
            end_date,
        )
        print(sums)
        return sums
