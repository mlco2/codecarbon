from contextlib import AbstractContextManager
from typing import List

from dependency_injector.providers import Callable
from sqlalchemy import and_, func

from carbonserver.api.domain.experiments import Experiments
from carbonserver.api.infra.database.sql_models import Emission as SqlModelEmission
from carbonserver.api.infra.database.sql_models import Experiment as SqlModelExperiment
from carbonserver.api.infra.database.sql_models import Run as SqlModelRun
from carbonserver.api.schemas import Experiment, ExperimentCreate, ExperimentReport


class SqlAlchemyRepository(Experiments):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
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
            experiments = []
            for e in res:
                experiment = self.map_sql_to_schema(e)
                experiments.append(experiment)
            return experiments

    def get_project_global_sums_by_experiment(self, project_id):
        with self.session_factory() as session:
            res = (
                session.query(
                    SqlModelExperiment.id.label("experiment_id"),
                    SqlModelExperiment.timestamp,
                    SqlModelExperiment.name,
                    SqlModelExperiment.description,
                    func.sum(SqlModelEmission.emissions_sum).label("emission_sum"),
                    func.sum(SqlModelEmission.energy_consumed).label("energy_consumed"),
                    func.sum(SqlModelEmission.duration).label("duration"),
                )
                .join(
                    SqlModelRun,
                    SqlModelExperiment.id == SqlModelRun.experiment_id,
                    isouter=True,
                )
                .join(
                    SqlModelEmission,
                    SqlModelRun.id == SqlModelEmission.run_id,
                    isouter=True,
                )
                .filter(SqlModelExperiment.project_id == project_id)
                .group_by(
                    SqlModelExperiment.id,
                    SqlModelExperiment.timestamp,
                    SqlModelExperiment.name,
                    SqlModelExperiment.description,
                )
                .all()
            )
            return res

    def get_project_detailed_sums_by_experiment(
        self, project_id, start_date, end_date
    ) -> List[ExperimentReport]:
        with self.session_factory() as session:
            res = (
                session.query(
                    SqlModelExperiment.id.label("experiment_id"),
                    SqlModelExperiment.timestamp,
                    SqlModelExperiment.name,
                    SqlModelExperiment.description,
                    SqlModelExperiment.country_name,
                    SqlModelExperiment.country_iso_code,
                    SqlModelExperiment.region,
                    SqlModelExperiment.on_cloud,
                    SqlModelExperiment.cloud_provider,
                    SqlModelExperiment.cloud_region,
                    func.sum(SqlModelEmission.emissions_sum).label("emissions"),
                    func.avg(SqlModelEmission.cpu_power).label("cpu_power"),
                    func.avg(SqlModelEmission.gpu_power).label("gpu_power"),
                    func.avg(SqlModelEmission.ram_power).label("ram_power"),
                    func.sum(SqlModelEmission.cpu_energy).label("cpu_energy"),
                    func.sum(SqlModelEmission.gpu_energy).label("gpu_energy"),
                    func.sum(SqlModelEmission.ram_energy).label("ram_energy"),
                    func.sum(SqlModelEmission.energy_consumed).label("energy_consumed"),
                    func.sum(SqlModelEmission.duration).label("duration"),
                    func.avg(SqlModelEmission.emissions_rate).label("emissions_rate"),
                    func.count(SqlModelEmission.emissions_rate).label(
                        "emissions_count"
                    ),
                )
                .join(
                    SqlModelRun,
                    SqlModelExperiment.id == SqlModelRun.experiment_id,
                    isouter=True,
                )
                .join(
                    SqlModelEmission,
                    SqlModelRun.id == SqlModelEmission.run_id,
                    isouter=True,
                )
                .filter(SqlModelExperiment.project_id == project_id)
                .filter(
                    and_(SqlModelEmission.timestamp >= start_date),
                    (SqlModelEmission.timestamp <= end_date),
                )
                .group_by(
                    SqlModelExperiment.id,
                    SqlModelExperiment.timestamp,
                    SqlModelExperiment.name,
                    SqlModelExperiment.description,
                    SqlModelExperiment.country_name,
                    SqlModelExperiment.country_iso_code,
                    SqlModelExperiment.region,
                    SqlModelExperiment.on_cloud,
                    SqlModelExperiment.cloud_provider,
                    SqlModelExperiment.cloud_region,
                )
                .all()
            )
            return res

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
