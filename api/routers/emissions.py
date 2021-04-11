from fastapi import APIRouter, Path, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_token_header, get_db
from database import crud_emissions
from database.schemas import EmissionCreate


router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


emissions_temp_db = []


@router.put("/emission", tags=["emissions"])
def add_emission(emission: EmissionCreate, db: Session = Depends(get_db)):
    # Remove next line when DB work
    emissions_temp_db.append(emission.dict())
    crud_emissions.save_emission(db, emission)


@router.get("/emission/{emission_id}", tags=["emissions"])
async def read_emission(
    emission_id: str = Path(..., title="The ID of the emission to get")
):
    emission = crud_emissions.get_one_emission(emission_id)
    if emission_id is False:
        raise HTTPException(status_code=404, detail="Item not found")
    return emission


@router.get("/emissions/{experiment_id}", tags=["emissions"])
async def read_experiment_emissions(
    experiment_id: str = Path(..., title="The ID of the experiment to get")
):
    experiment_emissions = crud_emissions.get_emissions_from_experiment(experiment_id)
    # Remove next line when DB work
    experiment_emissions = emissions_temp_db
    return experiment_emissions
