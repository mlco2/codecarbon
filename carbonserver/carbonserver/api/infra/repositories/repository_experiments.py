from typing import List

from carbonserver.api.domain.experiments import Experiments
from carbonserver.api.infra.database.sql_models import Experiment as SqlModelExperiment
from carbonserver.api.schemas import Experiment, ExperimentCreate


class SqlAlchemyRepository(Experiments):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def add_experiment(self, experiment: ExperimentCreate) -> Experiment:
        with self.session_factory() as session:
            db_experiment = SqlModelExperiment(
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

            session.add(db_experiment)
            session.commit()
            session.refresh(db_experiment)
            schema = self.map_sql_to_schema(db_experiment)
            return schema

    def get_one_experiment(self, experiment_id) -> Experiment:
        """Find the experiment in database and return it

        :experiment_id: The id of the experiment to retreive.
        :returns: An Experiment in pyDantic BaseModel format.
        :rtype: schemas.Experiment
        """
        with self.session_factory() as session:
            e = (
                session.query(SqlModelExperiment)
                .filter(SqlModelExperiment.id == experiment_id)
                .first()
            )
            if e is None:
                return None
            else:
                return self.map_sql_to_schema(e)

    def get_experiments_from_project(self, project_id) -> List[Experiment]:
        """Find the experiment from an emission in database and return it

        :project_id: The id of the project to retreive experiment from.
        :returns: An Experiment in pyDantic BaseModel format.
        :rtype: List[schemas.Experiment]
        """
        with self.session_factory() as session:
            res = session.query(SqlModelExperiment).filter(
                SqlModelExperiment.project_id == project_id
            )
            if res.first() is None:
                return []
            else:
                experiments = []
                for e in res:
                    experiment = self.map_sql_to_schema(e)
                    experiments.append(experiment)
                return experiments

    @staticmethod
    def map_sql_to_schema(experiment: SqlModelExperiment) -> Experiment:
        """Convert a models.Experiment to a schemas.Experiment

        :experiment: An Experiment in SQLAlchemy format.
        :returns: An Experiment in pyDantic BaseModel format.
        :rtype: schemas.Experiment
        """
        return Experiment(
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
