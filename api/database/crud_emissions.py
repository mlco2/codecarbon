# from uuid import uuid4 as uuid
from . import models, schemas
from sqlalchemy.orm import Session

# TODO : read https://fastapi.tiangolo.com/tutorial/sql-databases/

"""
Here there is all the method to manipulate the emissions data

# TODO:
 - Récupérationd d'une / des émission(s)
 - Pouvoir créer plusieurs émissions d'un coup
 - Créer crud_experiment, project, team, organizations



"""


def save_emission(db: Session, emission: schemas.EmissionCreate):
    # TODO : save emission in database and get her ID
    db_emission = models.Emission(
        timestamp=emission.timestamp,
        duration=emission.duration,
        emissions=emission.emissions,
        energy_consumed=emission.energy_consumed,
        country_name=emission.country_name,
        country_iso_code=emission.country_iso_code,
        region=emission.region,
        on_cloud=emission.on_cloud,
        cloud_provider=emission.cloud_provider,
        cloud_region=emission.cloud_region,
        experiment_id=emission.experiment_id,
    )
    db.add(db_emission)
    db.commit()
    db.refresh(db_emission)
    return db_emission


def get_one_emission(emission_id):
    # TODO : find the emission in database and return it
    return


def get_emissions_from_experiment(experiment_id):
    # TODO : get emissions from experiment id in database
    return
