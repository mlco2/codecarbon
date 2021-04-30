from carbonserver.api.dependencies import get_db, get_token_header
from carbonserver.database.schemas import ProjectCreate
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

router = APIRouter(
    dependencies=[Depends(get_token_header)],
)


projects_temp_db = []


@router.put("/project", tags=["projects"])
def add_project(project: ProjectCreate, db: Session = Depends(get_db)):
    # Remove next line when DB work
    # projects_temp_db.append(project.dict())
    # repository_projects = SqlAlchemyRepository(db)
    # repository_projects.add_save_emission(db, project)
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("/project/{project_id}", tags=["projects"])
async def read_project(
    project_id: str = Path(..., title="The ID of the project to get")
):
    # project = crud_projects.get_one_project(project_id)
    # if project_id is False:
    #     raise HTTPException(status_code=404, detail="Item not found")
    # return project
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("/projects/{project_id}", tags=["projects"])
async def read_experiment_projects(
    experiment_id: str = Path(..., title="The ID of the experiment to get")
):
    # experiment_projects = crud_projects.get_projects_from_experiment(experiment_id)
    # # Remove next line when DB work
    # experiment_projects = projects_temp_db
    # return experiment_projects
    raise HTTPException(status_code=501, detail="Not Implemented")
