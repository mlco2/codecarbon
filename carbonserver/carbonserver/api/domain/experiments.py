import abc
from typing import List

from carbonserver.api.schemas import Experiment, ExperimentCreate


class Experiments(abc.ABC):
    @abc.abstractmethod
    def add_experiment(self, experiment: ExperimentCreate) -> Experiment:
        raise NotImplementedError

    @abc.abstractmethod
    def get_one_experiment(self, experiment_id: str) -> Experiment:
        raise NotImplementedError

    @abc.abstractmethod
    def get_experiments_from_project(self, project_id) -> List[Experiment]:
        raise NotImplementedError
