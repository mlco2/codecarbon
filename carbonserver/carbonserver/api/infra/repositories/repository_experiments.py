from typing import List

from sqlalchemy.orm import Session

from carbonserver.api import schemas
from carbonserver.api.domain.experiments import Experiments
from carbonserver.database import models

"""
Here there is all the method to manipulate the experiment data
"""


class SqlAlchemyRepository(Experiments):
    def __init__(self, db: Session):
        self.db = db

    def add_experiment(self, experiment: schemas.ExperimentCreate):
        # TODO : save experiment in database and get her ID
        db_experiment = models.Experiment(
            timestamp=experiment.timestamp,
            name=experiment.name,
            description=experiment.description,
            country_name=experiment.country_name,
            country_iso_code=experiment.country_iso_code,
            region=experiment.region,
            on_cloud=experiment.on_cloud,
            cloud_provider=experiment.cloud_provider,
            cloud_region=experiment.cloud_region,
            project_id=experiment.project_id,
        )
        self.db.add(db_experiment)
        self.db.commit()
        self.db.refresh(db_experiment)
        return db_experiment

    def get_one_experiment(self, experiment_id):
        """Find the experiment in database and return it

        :experiment_id: The id of the experiment to retreive.
        :returns: An Experiment in pyDantic BaseModel format.
        :rtype: schemas.Experiment
        """
        e = (
            self.db.query(models.Experiment)
            .filter(models.Experiment.id == experiment_id)
            .first()
        )
        if e is None:
            return None
        else:
            return self.get_db_to_class(e)

    def get_experiments_from_project(self, project_id) -> List[schemas.Experiment]:
        """Find the experiment from an emission in database and return it

        :project_id: The id of the project to retreive experiment from.
        :returns: An Experiment in pyDantic BaseModel format.
        :rtype: List[schemas.Experiment]
        """
        res = self.db.query(models.Experiment).filter(
            models.Experiment.project_id == project_id
        )
        if res.first() is None:
            return []
        else:
            # Convert the table of models.Emission to a table of schemas.Emission
            experiments = []
            for e in res:
                experiment = self.get_db_to_class(e)
                experiments.append(experiment)
            return experiments

    @staticmethod
    def get_db_to_class(experiment: models.Experiment) -> schemas.Experiment:
        """Convert a models.Experiment to a schemas.Experiment

        :experiment: An Experiment in SQLAlchemy format.
        :returns: An Experiment in pyDantic BaseModel format.
        :rtype: schemas.Experiment
        """
        return schemas.Experiment(
            id=experiment.id,
            timestamp=experiment.timestamp,
            name=experiment.name,
            description=experiment.description,
            country_name=experiment.country_name,
            country_iso_code=experiment.country_iso_code,
            region=experiment.region,
            on_cloud=experiment.on_cloud,
            cloud_provider=experiment.cloud_provider,
            cloud_region=experiment.cloud_region,
            project_id=experiment.project_id,
        )


class InMemoryRepository(Experiments):
    def __init__(self):
        self.experiments: List = []
        self.id: int = 0

    def add_experiment(self, experiment: schemas.ExperimentCreate):
        self.experiments.append(
            models.Experiment(
                id=self.id + 1,
                timestamp=experiment.timestamp,
                name=experiment.name,
                description=experiment.description,
                country_name=experiment.country_name,
                country_iso_code=experiment.country_iso_code,
                region=experiment.region,
                on_cloud=experiment.on_cloud,
                cloud_provider=experiment.cloud_provider,
                cloud_region=experiment.cloud_region,
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
            country_name=experiment.country_name,
            country_iso_code=experiment.country_iso_code,
            region=experiment.region,
            on_cloud=experiment.on_cloud,
            cloud_provider=experiment.cloud_provider,
            cloud_region=experiment.cloud_region,
            project_id=experiment.project_id,
        )

    def get_experiments_from_project(self, project_id) -> List[schemas.Experiment]:
        experiments = []
        for experiment in self.experiments:
            print(experiment)
            if experiment.project_id == project_id:
                experiments.append(
                    schemas.Experiment(
                        id=experiment.id,
                        timestamp=experiment.timestamp,
                        name=experiment.name,
                        description=experiment.description,
                        country_name=experiment.country_name,
                        country_iso_code=experiment.country_iso_code,
                        region=experiment.region,
                        on_cloud=experiment.on_cloud,
                        cloud_provider=experiment.cloud_provider,
                        cloud_region=experiment.cloud_region,
                        project_id=project_id,
                    )
                )
        return experiments

    @staticmethod
    def get_db_to_class(experiment: models.Experiment) -> schemas.Experiment:
        return schemas.Experiment(
            id=experiment.id,
            timestamp=experiment.timestamp,
            name=experiment.name,
            description=experiment.description,
            isactive=experiment.energy_consumed,
            country_name=experiment.country_name,
            country_iso_code=experiment.country_iso_code,
            region=experiment.region,
            on_cloud=experiment.on_cloud,
            cloud_provider=experiment.cloud_provider,
            cloud_region=experiment.cloud_region,
            project_id=experiment.project_id,
        )
