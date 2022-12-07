from datetime import datetime, timedelta
from typing import List, Optional

import dateutil.relativedelta
from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import Run, RunCreate, RunReport
from carbonserver.api.services.run_service import RunService
from carbonserver.api.usecases.run.experiment_sum_by_run import (
    ExperimentSumsByRunUsecase,
)

RUNS_ROUTER_TAGS = ["Runs"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)
runs_temp_db = []


@router.post(
    "/run",
    tags=RUNS_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
    response_model=Run,
)
@inject
def add_run(
    run: RunCreate,
    run_service: RunService = Depends(Provide[ServerContainer.run_service]),
) -> Run:
    return run_service.add_run(run)


@router.get(
    "/run/{run_id}",
    tags=RUNS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=Run,
)
@inject
def read_run(
    run_id: str,
    run_service: RunService = Depends(Provide[ServerContainer.run_service]),
) -> Run:
    return run_service.read_run(run_id)


@router.get(
    "/runs",
    tags=RUNS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=List[Run],
)
@inject
def list_runs(
    run_service: RunService = Depends(Provide[ServerContainer.run_service]),
) -> List[Run]:
    return run_service.list_runs()


@router.get(
    "/runs/experiment/{experiment_id}",
    tags=RUNS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_runs_from_experiment(
    experiment_id: str,
    run_service: RunService = Depends(Provide[ServerContainer.run_service]),
):
    return run_service.list_runs_from_experiment(experiment_id)


@router.get(
    "/runs/{experiment_id}/sums/",
    tags=RUNS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_experiment_detailed_sums_by_run(
    experiment_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    experiment_global_sum_by_run_usecase: ExperimentSumsByRunUsecase = Depends(
        Provide[ServerContainer.experiment_sums_by_run_usecase],
    ),
) -> List[RunReport]:
    start_date = (
        start_date
        if start_date
        else datetime.now() - dateutil.relativedelta.relativedelta(months=3)
    )
    end_date = end_date if end_date else datetime.now() + timedelta(days=1)
    return experiment_global_sum_by_run_usecase.compute_detailed_sum(
        experiment_id,
        start_date,
        end_date,
    )


@router.get(
    "/lastrun/project/{project_id}",
    tags=RUNS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=Run,
)
@inject
def read_project_last_run(
    project_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    run_service: RunService = Depends(Provide[ServerContainer.run_service]),
) -> Run:
    start_date = (
        start_date
        if start_date
        else datetime.now() - dateutil.relativedelta.relativedelta(months=3)
    )
    end_date = end_date if end_date else datetime.now() + timedelta(days=1)
    return run_service.read_project_last_run(project_id, start_date, end_date)
