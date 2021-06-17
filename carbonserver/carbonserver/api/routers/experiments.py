from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import ExperimentCreate
from carbonserver.api.services.experiments_service import ExperimentService

EXPERIMENTS_ROUTER_TAGS = ["experiments"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.put(
    "/experiment/", tags=EXPERIMENTS_ROUTER_TAGS, status_code=status.HTTP_201_CREATED
)
@inject
def add_experiment(
    experiment: ExperimentCreate,
    experiment_service: ExperimentService = Depends(
        Provide[ServerContainer.experiment_service]
    ),
):
    return experiment_service.add_experiment(experiment)


@router.get(
    "/experiment/{experiment_id}",
    tags=EXPERIMENTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_experiment(
    experiment_id: str,
    experiment_service: ExperimentService = Depends(
        Provide[ServerContainer.experiment_service]
    ),
):
    return experiment_service.get_one_experiment(experiment_id)


@router.get(
    "/experiments/{experiment_id}",
    tags=EXPERIMENTS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_experiment_experiments(
    project_id: str,
    experiment_service: ExperimentService = Depends(
        Provide[ServerContainer.experiment_service]
    ),
):

    return experiment_service.get_experiments_from_project(project_id)
