from typing import List

from sqlalchemy import exc
from sqlalchemy.orm import Session

from carbonserver.api import schemas
from carbonserver.api.domain.experiments import Experiments
from carbonserver.api.errors import DBErrorEnum, DBError, DBException
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

        try:
            self.db.add(db_experiment)
            self.db.commit()
            self.db.refresh(db_experiment)
            return db_experiment
        except exc.IntegrityError as e:
            # Sample error : sqlalchemy.exc.IntegrityError: (psycopg2.errors.ForeignKeyViolation) insert or update on table "emissions" violates foreign key constraint "fk_emissions_runs"
            self.db.rollback()
            raise DBException(
                error=DBError(code=DBErrorEnum.INTEGRITY_ERROR, message=e.orig.args[0])
            )
        except exc.DataError as e:
            self.db.rollback()
            # Sample error :  sqlalchemy.exc.DataError: (psycopg2.errors.InvalidTextRepresentation) invalid input syntax for type uuid: "5050f55-406d-495d-830e-4fd12c656bd1"
            raise DBException(
                error=DBError(code=DBErrorEnum.DATA_ERROR, message=e.orig.args[0])
            )
        except exc.ProgrammingError as e:
            # sqlalchemy.exc.ProgrammingError: (psycopg2.ProgrammingError) can't adapt type 'SecretStr'
            self.db.rollback()
            raise DBException(
                error=DBError(
                    code=DBErrorEnum.PROGRAMMING_ERROR, message=e.orig.args[0]
                )
            )

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
