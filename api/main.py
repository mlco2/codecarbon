from fastapi import Depends, FastAPI
from dependencies import get_query_token
<<<<<<< HEAD
from routers import emissions, experiments, projects, organizations, teams
from database.database import engine
from database import models
=======
from routers import emissions #, experiments, projects , organizations, teams
from database.database import engine
from domain import models
>>>>>>> 4eb7bf2... Init repository


# TODO : read https://fastapi.tiangolo.com/tutorial/bigger-applications/


# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(dependencies=[Depends(get_query_token)])


app.include_router(emissions.router)
#app.include_router(experiments.router)
#app.include_router(projects.router)
#app.include_router(teams.router)
#app.include_router(organisations.router)

@app.get("/")
def default():
    return {"docs": "Please go to /docs"}


@app.get("/status")
def status():
    return {"status": "OK"}
