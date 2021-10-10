from carbonserver.api.infra.repositories.repository_experiments import (
    SqlAlchemyRepository,
)


class ProjectGlobalSumsByExperimentUsecase:
    def __init__(self, experiment_repository: SqlAlchemyRepository) -> None:
        self._experiment_repository = experiment_repository

    def compute(self, project_id: str):
        sums = self._experiment_repository.get_project_global_sums_by_experiment(
            project_id
        )
        return sums

    def compute_with_details(self, project_id: str):
        sums = self._experiment_repository.get_project_detailed_sums_by_experiment(
            project_id
        )
        return sums
