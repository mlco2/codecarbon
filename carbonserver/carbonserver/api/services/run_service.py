from typing import List
from uuid import UUID

from carbonserver.api.errors import NotAllowedError, NotAllowedErrorEnum, UserException
from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository
from carbonserver.api.schemas import Run, RunCreate, User
from carbonserver.api.services.auth_context import AuthContext


def _not_allowed() -> UserException:
    return UserException(
        NotAllowedError(
            code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
            message="Operation not authorized",
        )
    )


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
        run = self._repository.get_one_run(run_id)
        if not self._auth_context.can_read_experiment(run.experiment_id, user):
            raise _not_allowed()
        return run

    def list_runs(self, user: User) -> List[Run]:
        # Only runs the caller can access through an organization membership.
        return self._repository.list_runs_for_user(user.id)

    def list_runs_from_experiment(self, experiment_id: str, user: User = None):
        if not self._auth_context.can_read_experiment(experiment_id, user):
            raise _not_allowed()
        return self._repository.get_runs_from_experiment(experiment_id)

    def read_project_last_run(
        self, project_id: str, start_date, end_date, user: User = None
    ) -> Run:
        if not self._auth_context.can_read_project(project_id, user):
            raise _not_allowed()
        return self._repository.get_project_last_run(project_id, start_date, end_date)
