from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from carbonserver.api.dependencies import get_db, get_token_header
from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository
from carbonserver.api.schemas import RunCreate

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


@router.put("/run", tags=["runs"])
def add_run(run: RunCreate, db: Session = Depends(get_db)):
    repository_runs = SqlAlchemyRepository(db)
    db_run = repository_runs.add_run(run)
    return {"id": db_run.id}
    # TODO : Return Error when experiment does not exist
