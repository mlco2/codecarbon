import logging
from contextlib import AbstractContextManager, contextmanager
from typing import Callable

from sqlalchemy import create_engine, exc, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from carbonserver.api.errors import DBError, DBErrorEnum, DBException

logger = logging.getLogger(__name__)

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

    # Les exceptions de la base de données sont remontées ici, un switch case peut être mis en place pour remonter
    # les exceptions connues pour la base de données
    @contextmanager
    def session(self) -> Callable[..., AbstractContextManager]:
        session: Session = self._session_factory()
        try:
            yield session

        except exc.IntegrityError as e:
            session.rollback()
            raise DBException(
                error=DBError(code=DBErrorEnum.INTEGRITY_ERROR, message=e.orig.args[0])
            )
        except exc.DataError as e:
            session.rollback()
            raise DBException(
                error=DBError(code=DBErrorEnum.DATA_ERROR, message=e.orig.args[0])
            )
        except exc.ProgrammingError as e:
            session.rollback()
            raise DBException(
                error=DBError(
                    code=DBErrorEnum.PROGRAMMING_ERROR, message=e.orig.args[0]
                )
            )
        except Exception:
            logger.exception("Session rollback because of exception")
            session.rollback()
            raise
        finally:
            session.close()
