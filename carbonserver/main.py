from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from carbonserver.api.dependencies import get_query_token
from carbonserver.api.errors import DBException, UserException
from carbonserver.api.routers import (
    emissions,
    experiments,
    organizations,
    projects,
    runs,
    teams,
    users,
)
from carbonserver.database import models
from carbonserver.database.database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(dependencies=[Depends(get_query_token)])


@app.exception_handler(DBException)
async def db_exception_handler(request: Request, exc: DBException):
    return JSONResponse(
        status_code=422,
        content={
            "code": exc.error.code,
            "message": "Database error: " + exc.error.message,
        },
    )


@app.exception_handler(UserException)
async def user_exception_handler(request: Request, exc: UserException):
    return JSONResponse(
        status_code=403,
        content={
            "code": exc.error.code,
            "message": "Authentification error: " + exc.error.message,
        },
    )


app.include_router(emissions.router)
app.include_router(runs.router)
app.include_router(experiments.router)
app.include_router(projects.router)
app.include_router(teams.router)
app.include_router(organizations.router)
app.include_router(users.router)


@app.get("/")
def default():
    return {"docs": "Please go to /docs"}


@app.get("/status")
def status():
    return {"status": "OK"}
