from carbonserver.api.dependencies import get_db, get_token_header
from carbonserver.api.schemas import RunCreate
from carbonserver.api.infra.repositories.repository_runs import (
    SqlAlchemyRepository,
)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.put("/run", tags=["runs"], status_code=201)
def add_run(run: RunCreate, db: Session = Depends(get_db)):
    repository_runs = SqlAlchemyRepository(db)
    repository_runs.add_run(run)
    # TODO : Return Error when experiment does not exist
