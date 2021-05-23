from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from carbonserver.api.dependencies import get_db, get_token_header
from carbonserver.api.errors import DBError, DBException
from carbonserver.api.infra.repositories.repository_emissions import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import EmissionCreate

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.put("/emission", tags=["emissions"], status_code=201)
def add_emission(emission: EmissionCreate, db: Session = Depends(get_db)):
    repository_emissions = SqlAlchemyRepository(db)
    res = repository_emissions.add_emission(emission)
    if isinstance(res, DBError):
        raise DBException(error=res)


@router.get("/emission/{emission_id}", tags=["emissions"])
async def read_emission(
    emission_id: str = Path(..., title="The ID of the emission to get"),
    db: Session = Depends(get_db),
):
    repository_emissions = SqlAlchemyRepository(db)
    emission = repository_emissions.get_one_emission(emission_id)
    if emission is None:
        raise HTTPException(status_code=404, detail="Emission not found")
    return emission


@router.get("/emissions/{run_id}", tags=["emissions"])
async def read_experiment_emissions(
    run_id: str = Path(..., title="The ID of the experiment to get"),
    db: Session = Depends(get_db),
):
    repository_emissions = SqlAlchemyRepository(db)
    experiment_emissions = repository_emissions.get_emissions_from_run(run_id)
    if len(experiment_emissions) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Emission not found for run_id {run_id}",
        )
    return experiment_emissions
