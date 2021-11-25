from datetime import datetime
from typing import Any, List, Optional

import dateutil.relativedelta
from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import Experiment, ExperimentCreate
from carbonserver.api.services.experiments_service import ExperimentService
from carbonserver.api.usecases.experiment.project_global_sum_by_experiment import (
    ProjectGlobalSumsByExperimentUsecase,
)
from carbonserver.logger import logger

EXPERIMENTS_ROUTER_TAGS = ["Experiments"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.post(
    "/experiment",
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
    "/experiment/{experiment_id}",
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
) -> Experiment:
    return experiment_service.get_one_experiment(experiment_id)


@router.get(
    "/experiments/project/{project_id}",
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
) -> List[Experiment]:

    return experiment_service.get_experiments_from_project(project_id)


@router.get(
    "/experiments/{project_id}/global_sums/",
    tags=EXPERIMENTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_project_sums_by_experiment(
    project_id: str,
    project_global_sum_by_experiment_usecase: ProjectGlobalSumsByExperimentUsecase = Depends(
        Provide[ServerContainer.project_global_sum_by_experiment_usecase]
    ),
) -> Any:
    return project_global_sum_by_experiment_usecase.compute(project_id)


@router.get(
    "/experiments/{project_id}/detailed_sums/",
    tags=EXPERIMENTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_project_detailed_sums_by_experiment(
    project_id: str,
    start_date: Optional[datetime] = datetime.now()
    - dateutil.relativedelta.relativedelta(months=3),
    end_date: Optional[datetime] = datetime.now(),
    project_global_sum_by_experiment_usecase: ProjectGlobalSumsByExperimentUsecase = Depends(
        Provide[ServerContainer.project_global_sum_by_experiment_usecase]
    ),
) -> Any:
    return project_global_sum_by_experiment_usecase.compute_with_details(
        project_id, start_date, end_date
    )
