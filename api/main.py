from fastapi import Depends, FastAPI
from dependencies import get_query_token
from routers import emissions

# TODO : read https://fastapi.tiangolo.com/tutorial/bigger-applications/

app = FastAPI(dependencies=[Depends(get_query_token)])


app.include_router(emissions.router)


@app.get("/")
def default():
    return {"docs": "Please go to /docs"}


@app.get("/status")
def status():
    return {"status": "OK"}
