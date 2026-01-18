from datetime import datetime, timedelta
from typing import List, Optional, Union

import dateutil.relativedelta
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, File, UploadFile, Form
from starlette import status

from carbonserver.api.errors import EmptyResultException
from carbonserver.api.schemas import AccessLevel, Empty, Run, RunCreate, RunReport
from carbonserver.api.services.project_token_service import ProjectTokenService
from carbonserver.api.services.run_service import RunService
from carbonserver.api.usecases.run.experiment_sum_by_run import (
    ExperimentSumsByRunUsecase,
)
from carbonserver.container import ServerContainer
from carbonserver.logger import logger

RUNS_ROUTER_TAGS = ["Runs"]

router = APIRouter()
runs_temp_db = []


@router.post(
    "/runs",
    tags=RUNS_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
    response_model=Run,
)
@inject
def add_run(
    run: RunCreate,
    run_service: RunService = Depends(Provide[ServerContainer.run_service]),
    project_token_service: ProjectTokenService = Depends(
        Provide[ServerContainer.project_token_service]
    ),
    x_api_token: Optional[str] = Header(None),
) -> Run:

    project_token_service.project_token_has_access(
        AccessLevel.WRITE.value,
        experiment_id=run.experiment_id,
        project_token=x_api_token,
    )
    return run_service.add_run(run)


@router.get(
    "/runs/{run_id}",
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
    "/experiments/{experiment_id}/runs",
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
    "/experiments/{experiment_id}/runs/sums/",
    tags=RUNS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_experiment_detailed_sums_by_run(
    experiment_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    experiment_global_sum_by_run_usecase: ExperimentSumsByRunUsecase = Depends(
        Provide[ServerContainer.experiment_sums_by_run_usecase]
    ),
) -> List[RunReport]:
    start_date = (
        start_date
        if start_date
        else datetime.now() - dateutil.relativedelta.relativedelta(months=3)
    )
    end_date = end_date if end_date else datetime.now() + timedelta(days=1)
    return experiment_global_sum_by_run_usecase.compute_detailed_sum(
        experiment_id, start_date, end_date
    )


@router.get(
    "/lastrun/project/{project_id}",
    tags=RUNS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
    response_model=Union[Run, Empty],
)
@inject
def read_project_last_run(
    project_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    run_service: RunService = Depends(Provide[ServerContainer.run_service]),
) -> Union[Run, Empty]:
    start_date = (
        start_date
        if start_date
        else datetime.now() - dateutil.relativedelta.relativedelta(months=3)
    )
    end_date = end_date if end_date else datetime.now() + timedelta(days=1)
    try:
        return run_service.read_project_last_run(project_id, start_date, end_date)
    except EmptyResultException as e:
        logger.warning(f"read_project_last_run : {e}")
        return Empty()

@router.post(
    "/runs/remote",
    tags=RUNS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def run_remote(
    codecarbon_api_key: str = Form(...),
    experiment_id: str = Form(...),
    injected_code_file: UploadFile = File(..., description="Python code file to inject"),
    kaggle_api_key: str = Form(...),
    kaggle_username: str = Form(...),
    notebook_title: str = Form(...),
    api_endpoint: str = Form('https://api.codecarbon.io'),
    run_service: RunService = Depends(Provide[ServerContainer.run_service]),
) -> dict:
    try:
        # Read the file content as string
        # Seek to beginning in case file was partially read
        injected_code_file.file.seek(0)
        injected_code = injected_code_file.file.read().decode('utf-8')
        if not injected_code or not injected_code.strip():
            return {"status": "error", "message": "Uploaded file is empty"}, status.HTTP_400_BAD_REQUEST
        return run_service.run_remote(codecarbon_api_key, experiment_id, injected_code, kaggle_api_key, kaggle_username, notebook_title, api_endpoint)
    except Exception as e:
        logger.error(f"run_remote : {e}")
        return {"status": "error", "message": str(e)}