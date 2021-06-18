from typing import List

from container import ServerContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status

from carbonserver.api.dependencies import get_token_header
from carbonserver.api.schemas import Run, RunCreate
from carbonserver.api.services.run_service import RunService

RUNS_ROUTER_TAGS = ["runs"]

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)
runs_temp_db = []


@router.put(
    "/runs/",
    tags=RUNS_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
)
@inject
def add_run(
    run: RunCreate,
    run_service: RunService = Depends(Provide[ServerContainer.run_service]),
):
    return run_service.add_run(run)


@router.get(
    "/runs/{run_id}",
    tags=RUNS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def read_run(
    run_id: str,
    run_service: RunService = Depends(Provide[ServerContainer.run_service]),
) -> Run:
    return run_service.read_run(run_id)


@router.get(
    "/runs/",
    tags=RUNS_ROUTER_TAGS,
    status_code=status.HTTP_200_OK,
)
@inject
def list_runs(
    run_service: RunService = Depends(Provide[ServerContainer.run_service]),
) -> List[Run]:
    return run_service.list_run()


# @router.put("/run", tags=["runs"])
# def add_run(run: RunCreate, db: Session = Depends(get_db)):
#     repository_runs = SqlAlchemyRepository(db)
#     res = repository_runs.add_run(run)
#     if isinstance(res, DBError):
#         raise DBException(error=res)
#     else:
#         return {"id": res.id}
