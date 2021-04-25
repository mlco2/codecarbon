from fastapi import APIRouter, Path, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_token_header, get_db
from infra.repository.repository_emissions import SqlAlchemyRepository
from domain.schemas import EmissionCreate


router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.put("/emission", tags=["emissions"], status_code=201)
def add_emission(emission: EmissionCreate, db: Session = Depends(get_db)):
    repository_emissions = SqlAlchemyRepository(db)
    repository_emissions.add_save_emission(db, emission)


@router.get("/emission/{emission_id}", tags=["emissions"])
async def read_emission(
    emission_id: str = Path(..., title="The ID of the emission to get"),
    db: Session = Depends(get_db),
):
    repository_emissions = SqlAlchemyRepository(db)
    emission = repository_emissions.get_one_emission(db, emission_id)
    if emission is None:
        raise HTTPException(status_code=404, detail="Emission not found")
    return emission


@router.get("/emissions/{experiment_id}", tags=["emissions"])
async def read_experiment_emissions(
    experiment_id: str = Path(..., title="The ID of the experiment to get"),
    db: Session = Depends(get_db),
):
    repository_emissions = SqlAlchemyRepository(db)
    experiment_emissions = repository_emissions.get_emissions_from_experiment(
        db, experiment_id
    )
    if experiment_emissions is None:
        raise HTTPException(
            status_code=404,
            detail=f"Emission not found for experiment_id {experiment_id}",
        )
    return experiment_emissions
