import uuid
from contextlib import AbstractContextManager
from typing import List

from dependency_injector.providers import Callable

from carbonserver.api.domain.runs import Runs
from carbonserver.api.schemas import Run, RunCreate
from carbonserver.database.sql_models import Run as SqlModelRun

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
            )
            session.add(db_run)
            session.commit()
            session.refresh(db_run)
            return self.map_sql_to_schema(db_run)

    def get_one_run(self, run_id):
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

    def list_runs(self):
        with self.session_factory() as session:
            e = session.query(SqlModelRun)
            if e is None:
                return None
            else:
                runs: List[Run] = []
                for run in e:
                    runs.append(self.map_sql_to_schema(run))
                return runs

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
            emission_id=run.emission_id,
            experiment_id=run.experiment_id,
        )
