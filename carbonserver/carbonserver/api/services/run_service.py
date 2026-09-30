from typing import List
from uuid import UUID

from carbonserver.api.errors import NotAllowedError, NotAllowedErrorEnum, UserException
from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository
from carbonserver.api.schemas import Run, RunCreate, User
from carbonserver.api.services.auth_context import AuthContext
from carbonserver.api.services.matomo_tracker import MatomoTracker


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
        matomo_tracker: MatomoTracker | None = None,
    ):
        self._repository = run_repository
        self._auth_context = auth_context
        self._matomo_tracker = matomo_tracker

    def add_run(self, run: RunCreate, user: User = None) -> Run:
        created_run = self._repository.add_run(run)
        # The last step of the activation funnel: an experiment receiving its
        # first run shows someone actually integrated the package.
        if (
            self._matomo_tracker
            and self._matomo_tracker.enabled
            and self._repository.count_runs_from_experiment(run.experiment_id) == 1
        ):
            self._matomo_tracker.track_event("Activation", "first_run_received")
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
