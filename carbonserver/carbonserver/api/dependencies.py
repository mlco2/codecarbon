from typing import Optional

from fastapi import Header, HTTPException

from carbonserver.database.database import SessionLocal


async def get_token_header(
    x_token: Optional[str] = Header(
        "fake-super-secret-token", convert_underscores=False
    )
):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def get_query_token(token: Optional[str] = "jessica"):
    if token != "jessica":
        raise HTTPException(status_code=400, detail="No Jessica token provided")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
