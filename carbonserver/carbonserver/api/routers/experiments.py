from datetime import datetime, timedelta
from typing import List, Optional

import dateutil.relativedelta
from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import (
    AccessLevel,
    Experiment,
    ExperimentCreate,
    ExperimentReport,
)
from carbonserver.api.services.experiments_service import ExperimentService
from carbonserver.api.services.project_token_service import ProjectTokenService
from carbonserver.api.usecases.experiment.project_sum_by_experiment import (
    ProjectSumsByExperimentUsecase,
)
from carbonserver.logger import logger


def check_project_access(
    project_id: str,
    access_level: AccessLevel,
    project_token_service: ProjectTokenService = Depends(
        Provide[ServerContainer.project_token_service]
    ),
):
    project_token_service.project_token_has_access_to_project_id(
        access_level.value, project_id=project_id
    )


EXPERIMENTS_ROUTER_TAGS = ["Experiments"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.post(
    "/experiments",
    tags=EXPERIMENTS_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
    response_model=Experiment,
)
@inject
def add_experiment(
    experiment: ExperimentCreate,
    experiment_service: ExperimentService = Depends(
        Provide[ServerContainer.experiment_service]
    ),
) -> Experiment:
    experiment = experiment_service.add_experiment(experiment)
    logger.debug(f"Experiment added : {experiment}")
    return experiment


@router.get(
    "/experiments/{experiment_id}",
    tags=EXPERIMENTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=Experiment,
)
@inject
def read_experiment(
    experiment_id: str,
    experiment_service: ExperimentService = Depends(
        Provide[ServerContainer.experiment_service]
    ),
    project_token_service: ProjectTokenService = Depends(
        Provide[ServerContainer.project_token_service]
    ),
) -> Experiment:
    project_token_service.project_token_has_access_to_experiment_id(
        AccessLevel.READ.value, experiment_id=experiment_id
    )
    return experiment_service.get_one_experiment(experiment_id)


def get_project_access_dependency(access_level: AccessLevel, *args, **kwargs):
    def dependency():
        return check_project_access(*args, **kwargs, access_level=access_level)

    return dependency


@router.get(
    "/projects/{project_id}/experiments",
    tags=EXPERIMENTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=List[Experiment],
)
@inject
def read_project_experiments(
    project_id: str,
    experiment_service: ExperimentService = Depends(
        Provide[ServerContainer.experiment_service]
    ),
    verify_token_access=Depends(
        get_project_access_dependency(access_level=AccessLevel.READ)
    ),
) -> List[Experiment]:
    return experiment_service.get_experiments_from_project(project_id)


@router.get(
    "/projects/{project_id}/experiments/sums",
    tags=EXPERIMENTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_project_detailed_sums_by_experiment(
    project_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    project_global_sum_by_experiment_usecase: ProjectSumsByExperimentUsecase = Depends(
        Provide[ServerContainer.project_sums_by_experiment_usecase]
    ),
) -> List[ExperimentReport]:
    start_date = (
        start_date
        if start_date
        else datetime.now() - dateutil.relativedelta.relativedelta(months=3)
    )
    end_date = end_date if end_date else datetime.now() + timedelta(days=1)
    return project_global_sum_by_experiment_usecase.compute_detailed_sum(
        project_id, start_date, end_date
    )
