from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository
from carbonserver.api.schemas import Run, RunCreate


class RunService:
    def __init__(self, run_repository: SqlAlchemyRepository):
        self._repository = run_repository

    def add_run(self, run: RunCreate) -> Run:

        created_run = self._repository.add_run(run)
        return created_run

    def read_run(self, run_id: str) -> Run:
        return self._repository.get_one_run(run_id)

    def list_run(self):
        return self._repository.list_runs()
