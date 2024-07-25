from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

import dateutil.relativedelta
from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.schemas import Experiment, ExperimentCreate, ExperimentReport
from carbonserver.api.services.experiments_service import ExperimentService
from carbonserver.api.usecases.experiment.project_sum_by_experiment import (
    ProjectSumsByExperimentUsecase,
)
from carbonserver.carbonserver.api.errors import (
    NotAllowedError,
    NotAllowedErrorEnum,
    UserException,
)
from carbonserver.carbonserver.api.services.auth_service import UserWithAuthDependency

EXPERIMENTS_ROUTER_TAGS = ["Experiments"]

router = APIRouter()


@router.post(
    "/experiments",
    tags=EXPERIMENTS_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
    response_model=Experiment,
)
@inject
def add_experiment(
    organization_id: UUID,
    experiment: ExperimentCreate,
    auth_user: UserWithAuthDependency = Depends(UserWithAuthDependency),
    experiment_service: ExperimentService = Depends(
        Provide[ServerContainer.experiment_service]
    ),
) -> Experiment:
    if organization_id not in auth_user.db_user.organizations:
        raise UserException(
            NotAllowedError(
                code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
                message="Cannot add experiment from organization",
            )
        )
    else:
        experiment = experiment_service.add_experiment(experiment)
        return experiment


@router.get(
    "/experiments/{experiment_id}",
    tags=EXPERIMENTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=Experiment,
)
@inject
def read_experiment(
    organization_id: UUID,
    experiment_id: str,
    auth_user: UserWithAuthDependency = Depends(UserWithAuthDependency),
    experiment_service: ExperimentService = Depends(
        Provide[ServerContainer.experiment_service]
    ),
) -> Experiment:
    if organization_id not in auth_user.db_user.organizations:
        raise UserException(
            NotAllowedError(
                code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
                message="Cannot read experiment from organization",
            )
        )
    else:
        return experiment_service.get_one_experiment(experiment_id)


@router.get(
    "/projects/{project_id}/experiments",
    tags=EXPERIMENTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=List[Experiment],
)
@inject
def read_project_experiments(
    organization_id: UUID,
    project_id: str,
    auth_user: UserWithAuthDependency = Depends(UserWithAuthDependency),
    experiment_service: ExperimentService = Depends(
        Provide[ServerContainer.experiment_service]
    ),
) -> List[Experiment]:
    if organization_id not in auth_user.db_user.organizations:
        raise UserException(
            NotAllowedError(
                code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
                message="Cannot read experiment from project",
            )
        )
    else:
        return experiment_service.get_experiments_from_project(project_id)


@router.get(
    "/projects/{project_id}/experiments/sums",
    tags=EXPERIMENTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_project_detailed_sums_by_experiment(
    organization_id: UUID,
    project_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    auth_user: UserWithAuthDependency = Depends(UserWithAuthDependency),
    project_global_sum_by_experiment_usecase: ProjectSumsByExperimentUsecase = Depends(
        Provide[ServerContainer.project_sums_by_experiment_usecase]
    ),
) -> List[ExperimentReport]:
    if organization_id not in auth_user.db_user.organizations:
        raise UserException(
            NotAllowedError(
                code=NotAllowedErrorEnum.OPERATION_NOT_ALLOWED,
                message="Cannot add experiment from organization",
            )
        )
    else:
        start_date = (
            start_date
            if start_date
            else datetime.now() - dateutil.relativedelta.relativedelta(months=3)
        )
        end_date = end_date if end_date else datetime.now() + timedelta(days=1)
        return project_global_sum_by_experiment_usecase.compute_detailed_sum(
            project_id, start_date, end_date
        )
