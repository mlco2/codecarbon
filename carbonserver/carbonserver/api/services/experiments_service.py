from typing import List, Optional

from carbonserver.api.errors import NotAllowedError, NotAllowedErrorEnum, UserException
from carbonserver.api.infra.repositories.repository_experiments import (
    SqlAlchemyRepository as ExperimentSqlRepository,
)
from carbonserver.api.schemas import Experiment, ExperimentCreate, User
from carbonserver.api.services.auth_context import AuthContext


class ExperimentService:
    def __init__(
        self, experiment_repository: ExperimentSqlRepository, auth_context: AuthContext
    ):
        self._repository = experiment_repository
        self._auth_context = auth_context

    def add_experiment(self, experiment: ExperimentCreate, user: User) -> Experiment:
        if not self._auth_context.isOperationAuthorizedOnProject(
            experiment.project_id, user
        ):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Operation not authorized on organization",
                )
            )
        else:
            return self._repository.add_experiment(experiment)

    def get_one_experiment(self, experiment_id, user: Optional[User]) -> Experiment:
        experiment = self._repository.get_one_experiment(experiment_id)
        if not self._auth_context.can_read_project(experiment.project_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
                    message="Operation not authorized",
                )
            )
        else:
            return experiment

    def get_experiments_from_project(self, project_id, user: User) -> List[Experiment]:
        if not self._auth_context.can_read_project(project_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
                    message="Operation not authorized",
                )
            )
        else:
            return self._repository.get_experiments_from_project(project_id)
