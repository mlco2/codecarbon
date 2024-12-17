from typing import Optional

from fastapi import Header, HTTPException

from carbonserver.database.database import SessionLocal

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
