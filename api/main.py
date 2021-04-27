from database.database import engine
from dependencies import get_query_token
from domain import models
from fastapi import Depends, FastAPI
from routers import emissions  # , experiments, projects , organizations, teams

# TODO : read https://fastapi.tiangolo.com/tutorial/bigger-applications/


# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(dependencies=[Depends(get_query_token)])


app.include_router(emissions.router)
# app.include_router(experiments.router)
# app.include_router(projects.router)
# app.include_router(teams.router)
# app.include_router(organisations.router)


@app.get("/")
def default():
    return {"docs": "Please go to /docs"}


@app.get("/status")
def status():
    return {"status": "OK"}
