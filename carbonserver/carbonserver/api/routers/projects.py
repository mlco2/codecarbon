from carbonserver.api.dependencies import get_db, get_token_header
from carbonserver.api.schemas import ProjectCreate
from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository,
)
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


projects_temp_db = []


@router.put("/project", tags=["projects"])
def add_project(project: ProjectCreate, db: Session = Depends(get_db)):
    repository_projects = SqlAlchemyRepository(db)
    repository_projects.add_project(project)


@router.get("/project/{project_id}", tags=["projects"])
async def read_project(
    project_id: str = Path(..., title="The ID of the project to get"),
    db: Session = Depends(get_db),
):
    repository_projects = SqlAlchemyRepository(db)
    project = repository_projects.get_one_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return project


@router.get("/projects/{project_id}", tags=["projects"])
async def read_experiment_projects(
    experiment_id: str = Path(..., title="The ID of the experiment to get")
):
    # experiment_projects = crud_projects.get_projects_from_experiment(experiment_id)
    # # Remove next line when DB work
    # experiment_projects = projects_temp_db
    # return experiment_projects
    raise HTTPException(status_code=501, detail="Not Implemented")
