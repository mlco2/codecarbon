from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, exc, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from carbonserver.api.errors import DBError, DBErrorEnum, DBException
from carbonserver.logger import logger

Base = declarative_base()


class Database:
    def __init__(self, db_url: str) -> None:
        self._engine = create_engine(db_url, echo=True)
        self._session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            ),
        )

    def create_database(self) -> None:
        Base.metadata.create_all(self._engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session: Session = self._session_factory()
        try:
            yield session

        except exc.IntegrityError as e:
            session.rollback()
            logger.error(e.orig.args[0], exc_info=True)
            raise DBException(
                error=DBError(
                    code=DBErrorEnum.INTEGRITY_ERROR,
                    message="Relation not found, or duplicate key",
                )
            )
        except exc.DataError as e:
            session.rollback()
            logger.error(e.orig.args[0], exc_info=True)
            raise DBException(
                error=DBError(code=DBErrorEnum.DATA_ERROR, message="Invalid data")
            )
        except exc.ProgrammingError as e:
            session.rollback()
            logger.error(e.orig.args[0], exc_info=True)
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
