import uuid
from contextlib import AbstractContextManager
from typing import List

from dependency_injector.providers import Callable
from sqlalchemy import and_, func

from carbonserver.api.domain.runs import Runs
from carbonserver.api.infra.database.sql_models import Run as SqlModelRun
from carbonserver.api.infra.database.sql_models import Emission as SqlModelEmission
from carbonserver.api.schemas import Run, RunCreate, RunReport

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
                return None
            else:
                return self.map_sql_to_schema(e)

    def list_runs(self) -> List[Run]:
        with self.session_factory() as session:
            e = session.query(SqlModelRun)
            if e is None:
                return None
            else:
                runs: List[Run] = []
                for run in e:
                    runs.append(self.map_sql_to_schema(run))
                return runs

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
                return []
            else:
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
        :rtype: schemas.ProjectReport
        """
        with self.session_factory() as session:
            res = (
                session.query(
                    SqlModelRun.id.label("run_id"),
                    SqlModelRun.timestamp,
                    func.sum(SqlModelEmission.emissions_sum).label("emissions"),
                    func.sum(SqlModelEmission.cpu_power).label("cpu_power"),
                    func.sum(SqlModelEmission.gpu_power).label("gpu_power"),
                    func.sum(SqlModelEmission.ram_power).label("ram_power"),
                    func.sum(SqlModelEmission.cpu_energy).label("cpu_energy"),
                    func.sum(SqlModelEmission.gpu_energy).label("gpu_energy"),
                    func.sum(SqlModelEmission.ram_energy).label("ram_energy"),
                    func.sum(SqlModelEmission.energy_consumed).label("energy_consumed"),
                    func.sum(SqlModelEmission.duration).label("duration"),
                    func.sum(SqlModelEmission.emissions_rate).label(
                        "emissions_rate_sum"
                    ),
                    func.count(SqlModelEmission.emissions_rate).label(
                        "emissions_rate_count"
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
                    (SqlModelEmission.timestamp < end_date),
                )
                .group_by(
                    SqlModelRun.id,
                    SqlModelRun.timestamp,
                )
                .all()
            )
            return res
