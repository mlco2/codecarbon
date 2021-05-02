from carbonserver.database import schemas

import abc


class ExperimentInterface(abc.ABC):
    @abc.abstractmethod
    def save_experiment(self, experiment: schemas.ExperimentCreate):
        raise NotImplementedError

    @abc.abstractmethod
    def get_one_experiment(self, experiment_id):
        raise NotImplementedError

    @abc.abstractmethod
    def get_experiments_from_experiment(self, experiment_id):
        raise NotImplementedError
