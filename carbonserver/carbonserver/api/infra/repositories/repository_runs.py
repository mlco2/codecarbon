import uuid
from contextlib import AbstractContextManager
from typing import List, Union

from dependency_injector.providers import Callable
from fastapi import HTTPException
from sqlalchemy import and_, func

from carbonserver.api.domain.runs import Runs
from carbonserver.api.errors import EmptyResultException
from carbonserver.api.infra.database.sql_models import Emission as SqlModelEmission
from carbonserver.api.infra.database.sql_models import Experiment as SqlModelExperiment
from carbonserver.api.infra.database.sql_models import Project as SqlModelProject
from carbonserver.api.infra.database.sql_models import Run as SqlModelRun
from carbonserver.api.schemas import Run, RunCreate, RunReport
from carbonserver.logger import logger

"""
Here there is all the methods to manipulate the run data
"""


class SqlAlchemyRepository(Runs):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def add_run(self, run: RunCreate) -> Run:
        """Save an Run to the database.
        :run: An Run in pyDantic BaseModel format.
        :returns: An Run in SQLAlchemy Model format.
        :rtype: models.Run
        """
        with self.session_factory() as session:
            db_run = SqlModelRun(
                id=uuid.uuid4(),
                timestamp=run.timestamp,
                experiment_id=run.experiment_id,
                os=run.os,
                python_version=run.python_version,
                codecarbon_version=run.codecarbon_version,
                cpu_count=run.cpu_count,
                cpu_model=run.cpu_model,
                gpu_count=run.gpu_count,
                gpu_model=run.gpu_model,
                longitude=run.longitude,
                latitude=run.latitude,
                region=run.region,
                provider=run.provider,
                ram_total_size=run.ram_total_size,
                tracking_mode=run.tracking_mode,
            )
            session.add(db_run)
            session.commit()
            session.refresh(db_run)
            return self.map_sql_to_schema(db_run)

    def get_one_run(self, run_id) -> Run:
        """Find the run in database and return it

        :run_id: The id of the run to retreive.
        :returns: An Run in pyDantic BaseModel format.
        :rtype: schemas.Run
        """
        with self.session_factory() as session:
            e = session.query(SqlModelRun).filter(SqlModelRun.id == run_id).first()
            if e is None:
                raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
            return self.map_sql_to_schema(e)

    def list_runs(self) -> List[Run]:
        with self.session_factory() as session:
            res = session.query(SqlModelRun)
            if res is None:
                return []
            return [self.map_sql_to_schema(run) for run in res]

    def get_runs_from_experiment(self, experiment_id) -> List[Run]:
        """Find the list of runs from an experiment in database and return it

        :experiment_id: The id of the experiment to retreive runs from.
        :returns: List of Run in pyDantic BaseModel format.
        :rtype: List[schemas.Run]
        """
        with self.session_factory() as session:
            res = session.query(SqlModelRun).filter(
                SqlModelRun.experiment_id == experiment_id
            )
            if res.first() is None:
                raise EmptyResultException(f"No runs for experiment {experiment_id}")
            return [self.map_sql_to_schema(e) for e in res]

    @staticmethod
    def map_sql_to_schema(run: SqlModelRun) -> Run:
        """Convert a models.Run to a schemas.Run

        :emission: An Run in SQLAlchemy format.
        :returns: An Run in pyDantic BaseModel format.
        :rtype: schemas.Run
        """
        return Run(
            id=run.id,
            timestamp=run.timestamp,
            experiment_id=run.experiment_id,
            os=run.os,
            python_version=run.python_version,
            codecarbon_version=run.codecarbon_version,
            cpu_count=run.cpu_count,
            cpu_model=run.cpu_model,
            gpu_count=run.gpu_count,
            gpu_model=run.gpu_model,
            longitude=run.longitude,
            latitude=run.latitude,
            region=run.region,
            provider=run.provider,
            ram_total_size=run.ram_total_size,
            tracking_mode=run.tracking_mode,
        )

    def get_experiment_detailed_sums_by_run(
        self, experiment_id, start_date, end_date
    ) -> List[RunReport]:
        """Find the runs of an experiment in database between two dates and return
        a report containing the sum of their emissions

        :experiment_id: The id of the experiment to retrieve emissions from
        :start_date: the lower bound of the time interval which contains sought emissions
        :end_date: the upper bound of the time interval which contains sought emissions
        :returns: A report containing the sums of emissions
        :rtype: schemas.RunReport
        """
        with self.session_factory() as session:
            res = (
                session.query(
                    SqlModelRun.id.label("run_id"),
                    SqlModelRun.timestamp,
                    SqlModelRun.experiment_id,
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
                    SqlModelEmission,
                    SqlModelRun.id == SqlModelEmission.run_id,
                    isouter=True,
                )
                .filter(SqlModelRun.experiment_id == experiment_id)
                .filter(
                    and_(SqlModelEmission.timestamp >= start_date),
                    (SqlModelEmission.timestamp <= end_date),
                )
                .group_by(
                    SqlModelRun.id,
                    SqlModelRun.timestamp,
                )
                .all()
            )
            # TODO: Remove this log XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
            logger.debug(f"get_experiment_detailed_sums_by_run {res=}")
            if res is None:
                return []
            # Ca à l'air d'être le return qui n'est plus accepter car PyDantic refuse de
            # faire rentrer res dans RunReport
            return res

    def get_project_last_run(self, project_id, start_date, end_date) -> Union[Run]:
        """Find the last run of a project in database between two dates and return it

        :project_id: The id of the project to retrieve runs from
        :start_date: the lower bound of the time interval which contains sought runs
        :end_date: the upper bound of the time interval which contains sought runs
        :returns: A Run object
        :rtype: schemas.Run
        """
        with self.session_factory() as session:
            res = (
                session.query(SqlModelRun)
                .join(
                    SqlModelExperiment,
                    SqlModelExperiment.id == SqlModelRun.experiment_id,
                    isouter=True,
                )
                .join(
                    SqlModelProject, SqlModelProject.id == SqlModelExperiment.project_id
                )
                .filter(SqlModelProject.id == project_id)
                .filter(
                    and_(SqlModelRun.timestamp >= start_date),
                    (SqlModelRun.timestamp <= end_date),
                )
                .order_by(SqlModelRun.timestamp.desc())
                .first()
            )

            if res is None:
                logger.warning(
                    f"get_project_last_run : No runs for project {project_id}"
                )
                raise EmptyResultException(f"No runs for project {project_id}")
            return self.map_sql_to_schema(res)
