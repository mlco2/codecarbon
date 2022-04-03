from typing import List
from uuid import UUID

from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository
from carbonserver.api.schemas import Run, RunCreate


class RunService:
    def __init__(self, run_repository: SqlAlchemyRepository):
        self._repository = run_repository

    def add_run(self, run: RunCreate) -> Run:
        created_run = self._repository.add_run(run)
        return created_run

    def read_run(self, run_id: UUID) -> Run:
        return self._repository.get_one_run(run_id)

    def list_runs(self) -> List[Run]:
        return self._repository.list_runs()

    def list_runs_from_experiment(self, experiment_id: str):
        return self._repository.get_runs_from_experiment(experiment_id)

    def read_project_last_run(self, project_id: str, start_date, end_date) -> Run:
        return self._repository.get_project_last_run(project_id, start_date, end_date)
