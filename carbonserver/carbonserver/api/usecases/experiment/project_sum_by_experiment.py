from carbonserver.api.infra.repositories.repository_experiments import (
    SqlAlchemyRepository,
)


class ProjectSumsByExperimentUsecase:
    def __init__(self, experiment_repository: SqlAlchemyRepository) -> None:
        self._experiment_repository = experiment_repository

    def compute_detailed_sum(self, project_id: str, start_date, end_date):
        sums = self._experiment_repository.get_project_detailed_sums_by_experiment(
            project_id,
            start_date,
            end_date,
        )
        return sums
