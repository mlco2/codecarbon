import uuid
from typing import List

from carbonserver.api.services.user_service import UserService
from sqlalchemy import exc
from sqlalchemy.orm import Session

from carbonserver.api.domain.users import Users
from carbonserver.api.errors import DBError, DBErrorEnum, DBException
from carbonserver.api.schemas import User, UserCreate
from carbonserver.database.sql_models import User as SqlModelUser


class SqlAlchemyRepository(Users):
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user: UserCreate) -> User:
        """Creates an user in the database
        :returns: An User in pyDantic BaseModel format.
        :rtype: schemas.User
        """
        db_user = SqlModelUser(
            user_id=uuid.uuid4(),
            name=user.name,
            email=user.email,
            hashed_password=user.password,
            api_key=UserService.api_key_generator(),
            is_active=True,
        )
        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return self.get_db_to_class(db_user)

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

    def get_user_by_id(self, user_id: str) -> User:
        """Find an user in database and retrieves it

        :user_id: The id of the user to retrieve.
        :returns: An User in pyDantic BaseModel format.
        :rtype: schemas.User
        """
        e = self.db.query(SqlModelUser).filter(SqlModelUser.id == user_id).first()
        if e is None:
            return None
        else:
            return self.get_db_to_class(e)

    def list_users(self) -> List[User]:
        e = self.db.query(SqlModelUser)
        if e is None:
            return None
        else:
            users = []
            for user in e:
                users.append(self.get_db_to_class(user))
            return users

    @staticmethod
    def get_db_to_class(sql_user: SqlModelUser) -> User:
        """Sql To Pydantic Mapper

        :returns: An User in pyDantic BaseModel format.
        :rtype: schemas.User
        """
        return User(
            id=sql_user.user_id,
            name=sql_user.name,
            email=sql_user.email,
            hashed_password=sql_user.hashed_password,
            api_key=sql_user.api_key,
            is_active=sql_user.is_active,
        )


class InMemoryRepository(Users):
    def __init__(self):
        self.users: List[Users] = []
        self.id: int = 0
        self.inactive_users: List = []

    def create_user(self, user: UserCreate) -> SqlModelUser:
        self.id += 1
        self.users.append(
            SqlModelUser(
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
    def get_db_to_class(user: SqlModelUser) -> User:
        return User(
            id=user.user_id,
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            api_key=user.api_key,
            is_active=user.is_active,
        )
