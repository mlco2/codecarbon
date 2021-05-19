from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from carbonserver.config import settings

engine_kwargs = {}
if "sqlite" in settings.db_url:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
engine = create_engine(settings.db_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# We will use the function declarative_base() that returns a class.
# Later we will inherit from this class to create each of the database models or classes (the ORM models)
Base = declarative_base()
