import uuid
from contextlib import AbstractContextManager
from typing import List

from dependency_injector.providers import Callable

from carbonserver.api.domain.runs import Runs
from carbonserver.api.infra.database.sql_models import Run as SqlModelRun
from carbonserver.api.schemas import Run, RunCreate

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
                runs = []
                for e in res:
                    run = self.map_sql_to_schema(e)
                    runs.append(run)
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
            experiment_id=run.experiment_id,
        )
