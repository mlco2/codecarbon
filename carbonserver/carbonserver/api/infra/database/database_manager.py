from contextlib import AbstractContextManager, contextmanager
from typing import Callable

from sqlalchemy import create_engine, exc, orm
from sqlalchemy.orm import Session, declarative_base

from carbonserver.api.errors import DBError, DBErrorEnum, DBException
from carbonserver.logger import logger

Base = declarative_base()


class Database:
    def __init__(self, db_url: str) -> None:
        logger.info("Initializing database connection", extra={"db_url": db_url})
        self._engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        self._session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            ),
        )

    def create_database(self) -> None:
        logger.info("Creating database tables")
        Base.metadata.create_all(self._engine)

    @contextmanager
    def session(self) -> Callable[..., AbstractContextManager]:
        session: Session = self._session_factory()
        logger.debug("Opening database session")
        try:
            yield session
            session.commit()
            logger.debug("Database session completed successfully")
        except exc.IntegrityError as e:
            session.rollback()
            logger.error(
                "Integrity error - rolling back session",
                extra={"error": str(e.orig.args[0])},
                exc_info=True,
            )
            raise DBException(
                error=DBError(
                    code=DBErrorEnum.INTEGRITY_ERROR,
                    message="Relation not found, or duplicate key",
                )
            )
        except exc.DataError as e:
            session.rollback()
            logger.error(
                "Data error - rolling back session",
                extra={"error": str(e.orig.args[0])},
                exc_info=True,
            )
            raise DBException(
                error=DBError(code=DBErrorEnum.DATA_ERROR, message="Invalid data")
            )
        except exc.ProgrammingError as e:
            session.rollback()
            logger.error(
                "Programming error - rolling back session",
                extra={"error": str(e.orig.args[0])},
                exc_info=True,
            )
            raise DBException(
                error=DBError(
                    code=DBErrorEnum.PROGRAMMING_ERROR, message="Wrong schema"
                )
            )
        except Exception:
            logger.error("Session rollback because of exception", exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()
            logger.debug("Database session closed")