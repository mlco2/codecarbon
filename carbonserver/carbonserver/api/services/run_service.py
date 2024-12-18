from typing import List
from uuid import UUID

from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository
from carbonserver.api.schemas import Run, RunCreate, User
from carbonserver.api.services.auth_context import AuthContext


class RunService:
    def __init__(
        self,
        run_repository: SqlAlchemyRepository,
        auth_context: AuthContext,
    ):
        self._repository = run_repository
        self._auth_context = auth_context

    def add_run(self, run: RunCreate, user: User = None) -> Run:
        created_run = self._repository.add_run(run)
        return created_run

    def read_run(self, run_id: UUID, user: User = None) -> Run:
        return self._repository.get_one_run(run_id)

    def list_runs(self, user: User = None) -> List[Run]:
        return self._repository.list_runs()

    def list_runs_from_experiment(self, experiment_id: str, user: User = None):
        return self._repository.get_runs_from_experiment(experiment_id)

    def read_project_last_run(
        self, project_id: str, start_date, end_date, user: User = None
    ) -> Run:
        return self._repository.get_project_last_run(project_id, start_date, end_date)
