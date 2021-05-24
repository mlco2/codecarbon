from carbonserver.api.dependencies import get_query_token
from container import ServerContainer
from fastapi import FastAPI, Depends

from carbonserver.api.routers import users
from carbonserver.database import sql_models
from carbonserver.database.database import engine

routers = [
    users.router,
]


def create_app() -> FastAPI:

    container = init_container()

    init_db(container)
    server = init_server(container)
    return server


def init_container():
    container = ServerContainer()
    container.wire(modules=[users])
    return container


def init_db(container):
    db = container.db()
    db.create_database()
    sql_models.Base.metadata.create_all(bind=engine)


def init_server(container):
    server = FastAPI(dependencies=[Depends(get_query_token)])
    server.container = container
    server.include_router(users.router)

    return server


app = create_app()
