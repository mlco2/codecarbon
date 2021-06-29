from typing import List

from carbonserver.api.infra.repositories.repository_experiments import (
    SqlAlchemyRepository as ExperimentSqlRepository,
)
from carbonserver.api.schemas import Experiment, ExperimentCreate


class ExperimentService:
    def __init__(self, experiment_repository: ExperimentSqlRepository):
        self._repository = experiment_repository

    def add_experiment(self, experiment_id: ExperimentCreate) -> Experiment:
        experiment_id = self._repository.add_experiment(experiment_id)
        return experiment_id

    def get_one_experiment(self, experiment_id) -> Experiment:
        experiment = self._repository.get_one_experiment(experiment_id)
        return experiment

    def get_experiments_from_project(self, project_id) -> List[Experiment]:
        experiments = self._repository.get_experiments_from_project(project_id)
        return experiments
