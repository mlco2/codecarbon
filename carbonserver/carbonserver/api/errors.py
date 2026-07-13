from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException


class EmptyResultException(Exception):
    """
    The request return an empty result.
    """


class AuthenticationError(HTTPException):
    """
    Raised when a session cookie or bearer token cannot be verified
    (bad/absent signature, expired, or otherwise untrusted).

    Subclasses HTTPException so Starlette's built-in handler turns it into a
    real 401 response instead of the catch-all 500 handler in main.py.
    """

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=401,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


@dataclass
class ErrorBase:
    code: str
    message: str


class DBErrorEnum(Enum):
    INTEGRITY_ERROR = "INTEGRITY_ERROR"
    DATA_ERROR = "DATA_ERROR"
    PROGRAMMING_ERROR = "PROGRAMMING_ERROR"


class DBError(ErrorBase):
    code: DBErrorEnum


class DBException(Exception):
    def __init__(self, error):
        self.error = error


class UserErrorEnum(str, Enum):
    API_KEY_UNKNOWN = "API_KEY_UNKNOWN"
    API_KEY_DISABLE = "API_KEY_DISABLE"
    FORBIDDEN = "FORBIDDEN"


class UserError(ErrorBase):
    code: DBErrorEnum


class NotAllowedErrorEnum(str, Enum):
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    NOT_IN_ORGANISATION = "NOT_IN_ORGANISATION"
    NOT_IN_PROJECT = "NOT_IN_PROJECT"


class NotAllowedError(ErrorBase):
    code: NotAllowedErrorEnum


class NotFoundErrorEnum(str, Enum):
    NOT_FOUND = "NOT_FOUND"


class NotFoundError(ErrorBase):
    code: NotFoundErrorEnum


class UserException(Exception):
    def __init__(self, error):
        self.error = error


def get_http_exception(exception) -> HTTPException:
    """
    take an internal exception and return a HTTPException
    """
    if isinstance(exception, UserException):
        if isinstance(error := exception.error, NotAllowedError):
            return HTTPException(status_code=403, detail=error.message)
        elif isinstance(error := exception.error, NotFoundError):
            return HTTPException(status_code=404, detail=error.message)
    return HTTPException(status_code=500)
