from container import ServerContainer
from fastapi import FastAPI

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
    container.wire(modules=[routers])
    return container


def init_db(container):
    db = container.db()
    db.create_database()
    sql_models.Base.metadata.create_all(bind=engine)


def init_server(container):
    server = FastAPI()
    server.container = container

    @app.get("/")
    def default():
        return {"docs": "Please go to /docs"}

    @app.get("/status")
    def status():
        return {"status": "OK"}

    server.include_router(users.router)

    return server


if __name__ == "__main__":
    app = create_app()
