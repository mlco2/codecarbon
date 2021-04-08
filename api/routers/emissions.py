from fastapi import APIRouter, Path, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from dependencies import get_token_header
from database import emissions


router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


emissions_temp_db = []


class Emission(BaseModel):
    timestamp: datetime
    experiment_id: str
    project_name: str
    duration: int = Field(
        ..., gt=0, description="The duration must be greater than zero"
    )
    emissions: float = Field(
        ..., gt=0, description="The emissions must be greater than zero"
    )
    energy_consumed: float = Field(
        ..., gt=0, description="The energy_consumed must be greater than zero"
    )
    country_name: Optional[str] = None
    country_iso_code: Optional[str] = None
    region: Optional[str] = None
    on_cloud: bool
    cloud_provider: Optional[str] = None
    cloud_region: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2021-04-04T08:43:00+02:00",
                "experiment_id": "40088f1a-d28e-4980-8d80-bf5600056a14",
                "project_name": "skynet",
                "duration": 98745,
                "emissions": 1.548444,
                "energy_consumed": 57.21874,
                "country_name": "France",
                "country_iso_code": "FRA",
                "region": "france",
                "on_cloud": True,
                "cloud_provider": "aws",
                "cloud_region": "eu-west-1a",
            }
        }


@router.post("/emission", tags=["emissions"])
def add_emission(emission: Emission):
    # Remove next line when DB work
    emissions_temp_db.append(emission.dict())
    emission_id = emissions.save_emission(emission)
    return {"emission_id": emission_id}


@router.get("/emission/{emission_id}", tags=["emissions"])
async def read_emission(
    emission_id: str = Path(..., title="The ID of the emission to get")
):
    emission = emissions.get_one_emission(emission_id)
    if emission_id is False:
        raise HTTPException(status_code=404, detail="Item not found")
    return emission


@router.get("/emissions/{experiment_id}", tags=["emissions"])
async def read_experiment_emissions(
    experiment_id: str = Path(..., title="The ID of the experiment to get")
):
    experiment_emissions = emissions.get_emissions_from_experiment(experiment_id)
    # Remove next line when DB work
    experiment_emissions = emissions_temp_db
    return experiment_emissions
