import secrets
import uuid
from typing import List

from sqlalchemy import exc
from sqlalchemy.orm import Session

from carbonserver.api import schemas
from carbonserver.api.domain.users import Users
from carbonserver.api.errors import DBError, DBErrorEnum, DBException
from carbonserver.database.sql_models import User as ModelUser


class SqlAlchemyRepository(Users):
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user: schemas.UserCreate) -> ModelUser:
        db_user = ModelUser(
            user_id=uuid.uuid4(),
            name=user.name,
            email=user.email,
            hashed_password=user.password,
            api_key=_api_key_generator(),
            is_active=True,
        )
        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return db_user

        except exc.IntegrityError as e:
            # Sample error : sqlalchemy.exc.IntegrityError: (psycopg2.errors.ForeignKeyViolation) insert or update on table "emissions" violates foreign key constraint "fk_emissions_runs"
            self.db.rollback()
            raise DBException(
                error=DBError(code=DBErrorEnum.INTEGRITY_ERROR, message=e.orig.args[0])
            )
        except exc.DataError as e:
            self.db.rollback()
            # Sample error :  sqlalchemy.exc.DataError: (psycopg2.errors.InvalidTextRepresentation) invalid input syntax for type uuid: "5050f55-406d-495d-830e-4fd12c656bd1"
            raise DBException(
                error=DBError(code=DBErrorEnum.DATA_ERROR, message=e.orig.args[0])
            )
        except exc.ProgrammingError as e:
            # sqlalchemy.exc.ProgrammingError: (psycopg2.ProgrammingError) can't adapt type 'SecretStr'
            self.db.rollback()
            raise DBException(
                error=DBError(
                    code=DBErrorEnum.PROGRAMMING_ERROR, message=e.orig.args[0]
                )
            )

    def get_user_by_id(self, user_id) -> ModelUser:
        """Find an user in database and ModelUser it

        :user_id: The id of the user to retrieve.
        :returns: An User in pyDantic BaseModel format.
        :rtype: schemas.User
        """
        e = self.db.query(Users).filter(ModelUser.id == user_id).first()
        if e is None:
            return None
        else:
            return self.get_db_to_class(e)

    def list_users(self) -> List[schemas.User]:
        e = self.db.query(Users)
        if e is None:
            return None
        else:
            users = []
            for user in e:
                users.append(self.get_db_to_class(user))
            return users

    @staticmethod
    def get_db_to_class(user: ModelUser) -> schemas.User:
        return schemas.User(
            id=user.user_id,
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            api_key=user.api_key,
            is_active=user.is_active,
        )


class InMemoryRepository(Users):
    def __init__(self):
        self.users: List[Users] = []
        self.id: int = 0
        self.inactive_users: List = []

    def create_user(self, user: schemas.UserCreate) -> ModelUser:
        self.id += 1
        self.users.append(
            ModelUser(
                user_id=self.id,
                name=user.name,
                email=user.email,
                hashed_password=user.password,
                api_key=_api_key_generator(),
                is_active=True,
            )
        )
        return self.users[self.id - 1]

    def get_user_by_id(self, user_id: int):
        user = [user for user in self.users if user.user_id == user_id][0]
        return user

    def list_users(self):
        return self.users

    @staticmethod
    def get_db_to_class(user: ModelUser) -> schemas.User:
        return schemas.User(
            id=user.user_id,
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            api_key=user.api_key,
            is_active=user.is_active,
        )


def _api_key_generator():
    generated_key = secrets.token_urlsafe(16)
    return generated_key
