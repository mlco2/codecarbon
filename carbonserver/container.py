from dependency_injector import containers, providers

from carbonserver.api.infra.database.database_manager import Database
from carbonserver.api.infra.repositories import (
    repository_emissions,
    repository_experiments,
    repository_organizations,
    repository_projects,
    repository_projects_tokens,
    repository_runs,
    repository_users,
)
from carbonserver.api.services.auth_context import AuthContext
from carbonserver.api.services.emissions_service import EmissionService
from carbonserver.api.services.experiments_service import ExperimentService
from carbonserver.api.services.organization_service import OrganizationService
from carbonserver.api.services.project_service import ProjectService
from carbonserver.api.services.project_token_service import ProjectTokenService
from carbonserver.api.services.run_service import RunService
from carbonserver.api.services.signup_service import SignUpService
from carbonserver.api.services.user_service import UserService
from carbonserver.api.usecases.experiment.project_sum_by_experiment import (
    ProjectSumsByExperimentUsecase,
)
from carbonserver.api.usecases.organization.organization_sum import (
    OrganizationSumsUsecase,
)
from carbonserver.api.usecases.project.project_sum import ProjectSumsUsecase
from carbonserver.api.usecases.run.experiment_sum_by_run import (
    ExperimentSumsByRunUsecase,
)
from carbonserver.config import settings


class ServerContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    db_url = settings.db_url
    db = providers.Singleton(
        Database,
        db_url=db_url,
    )
    emission_repository = providers.Factory(
        repository_emissions.SqlAlchemyRepository,
        session_factory=db.provided.session,
    )

    experiment_repository = providers.Factory(
        repository_experiments.SqlAlchemyRepository,
        session_factory=db.provided.session,
    )

    project_repository = providers.Factory(
        repository_projects.SqlAlchemyRepository,
        session_factory=db.provided.session,
    )
    project_token_repository = providers.Factory(
        repository_projects_tokens.SqlAlchemyRepository,
        session_factory=db.provided.session,
    )

    user_repository = providers.Factory(
        repository_users.SqlAlchemyRepository,
        session_factory=db.provided.session,
    )

    organization_repository = providers.Factory(
        repository_organizations.SqlAlchemyRepository,
        session_factory=db.provided.session,
    )

    auth_context = providers.Factory(
        AuthContext,
        user_repository=user_repository,
        token_repository=project_token_repository,
    )

    emission_service = providers.Factory(
        EmissionService,
        emission_repository=emission_repository,
    )

    experiment_service = providers.Factory(
        ExperimentService,
        auth_context=auth_context,
        experiment_repository=experiment_repository,
    )

    project_sums_by_experiment_usecase = providers.Factory(
        ProjectSumsByExperimentUsecase,
        experiment_repository=experiment_repository,
    )

    project_sums_usecase = providers.Factory(
        ProjectSumsUsecase, project_repository=project_repository
    )

    project_service = providers.Factory(
        ProjectService,
        auth_context=auth_context,
        project_repository=project_repository,
    )

    project_token_service = providers.Factory(
        ProjectTokenService,
        project_token_repository=project_token_repository,
    )

    run_repository = providers.Factory(
        repository_runs.SqlAlchemyRepository,
        session_factory=db.provided.session,
    )

    experiment_sums_by_run_usecase = providers.Factory(
        ExperimentSumsByRunUsecase,
        run_repository=run_repository,
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
    )

    organization_service = providers.Factory(
        OrganizationService,
        auth_context=auth_context,
        organization_repository=organization_repository,
        user_repository=user_repository,
    )

    organization_sums_usecase = providers.Factory(
        OrganizationSumsUsecase,
        organization_repository=organization_repository,
    )

    run_service = providers.Factory(
        RunService,
        run_repository=run_repository,
    )

    sign_up_service = providers.Factory(
        SignUpService,
        user_repository=user_repository,
        organization_repository=organization_repository,
        project_repository=project_repository,
    )
