from typing import List
from carbonserver.api.infra.repositories.repository_experiments import (
    SqlAlchemyRepository as ExperimentRepository,
)
from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository as ProjectRepository,
)

from carbonserver.api.infra.repositories.users.sql_repository import (
    SqlAlchemyRepository as UserRepository,
)

from carbonserver.api.schemas import Experiment, ExperimentCreate

from carbonserver.carbonserver.api.errors import UserException, NotAllowedError, NotAllowedErrorEnum
from carbonserver.carbonserver.api.schemas import User


class ExperimentService:
    def __init__(
        self,
        experiment_repository: ExperimentRepository,
        user_repository: UserRepository,
        project_repository: ProjectRepository,
    ):
        self._experiment_repository = experiment_repository
        self._user_repository = user_repository
        self._project_repository = project_repository

    def add_experiment(self, experiment: ExperimentCreate) -> Experiment:
        if not self.isOperationAuthorizedOnProject(experiment.project_id, experiment.user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot add experiment to project from this organization.",
                )
            )
        experiment = self._experiment_repository.add_experiment(experiment)
        return experiment

    def get_one_experiment(self, experiment_id, user: User) -> Experiment:
        experiment = self._experiment_repository.get_one_experiment(experiment_id)
        if not self.isOperationAuthorizedOnProject(experiment.project_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot read experiment from this organization.",
                )
            )

        return experiment

    def get_experiments_from_project(self, project_id, user: User) -> List[Experiment]:
        if not self.isOperationAuthorizedOnProject(project_id, user):
            raise UserException(
                NotAllowedError(
                    code=NotAllowedErrorEnum.NOT_IN_ORGANISATION,
                    message="Cannot add experiment to project from this organization.",
                )
            )
        experiments = self._experiment_repository.get_experiments_from_project(project_id)
        return experiments

    def isOperationAuthorizedOnProject(self, project_id, user):
        return self._user_repository.is_user_authorized_on_project(project_id, user.id)
