# from uuid import uuid4 as uuid
from typing import List

from carbonserver.api.domain.experiment import ExperimentInterface
from carbonserver.database import schemas, models

from sqlalchemy.orm import Session

# TODO : read https://fastapi.tiangolo.com/tutorial/sql-databases/

"""
Here there is all the method to manipulate the experiment data
"""


class SqlAlchemyRepository(ExperimentInterface):
    def __init__(self, db: Session):
        self.db = db

    def save_experiment(self, experiment: schemas.ExperimentCreate):
        # TODO : save experiment in database and get her ID
        db_experiment = models.Experiment(
            timestamp=experiment.timestamp,
            name=experiment.name,
            description=experiment.description,
            is_active=experiment.is_active,
            project_id=experiment.project_id,
        )
        self.db.add(db_experiment)
        self.db.commit()
        self.db.refresh(db_experiment)
        return db_experiment

    def get_one_experiment(self, experiment_id):
        # TODO : find the experiment in database and return it

        return True

    def get_experiments_from_experiment(self, experiment_id):
        # TODO : get experiments from experiment id in database
        return True


class InMemoryRepository(ExperimentInterface):
    def __init__(self):
        self.experiments: List = []
        self.id: int = 0

    def save_experiment(self, experiment: schemas.ExperimentCreate):
        self.experiments.append(
            models.Experiment(
                id=self.id + 1,
                timestamp=experiment.timestamp,
                name=experiment.name,
                description=experiment.description,
                is_active=experiment.is_active,
                project_id=experiment.project_id,
            )
        )

    def get_one_experiment(self, experiment_id: int) -> schemas.Experiment:
        experiment = self.experiments[0]
        return schemas.Experiment(
            id=experiment.id,
            timestamp=experiment.timestamp,
            name=experiment.name,
            description=experiment.description,
            is_active=experiment.is_active,
            project_id=experiment.project_id,
        )

    def get_experiments_from_experiment(self, experiment_id):
        experiments = []
        for experiment in self.experiments:
            experiments.append(
                schemas.Experiment(
                    id=experiment.id,
                    timestamp=experiment.timestamp,
                    name=experiment.name,
                    description=experiment.description,
                    is_active=experiment.is_active,
                    project_id=experiment.project_id,
                )
            )
        return experiments
