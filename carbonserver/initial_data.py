"""
Import initial data used for develop e2e api tests
The most important is the main user with a known id
We can then forge an access token and use the API for testing
"""

import logging

from carbonserver.api.infra.database.database_manager import Database
from carbonserver.api.infra.database.sql_models import User as SqlModelUser
from carbonserver.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_initial_data(db):
    if settings.environment not in ("develop", "local"):
        raise Exception("This script must be run in develop environment")

    logger.info("Checking initial data...")
    MAIN_USER_ID = "bb479cc8-3357-4859-985d-e3cc209d6fc9"
    with db.session() as session:
        e = session.query(SqlModelUser).filter(SqlModelUser.id == MAIN_USER_ID).first()
        if e is None:
            logger.info("User not found. Creating...")
            db_user = SqlModelUser(
                id=MAIN_USER_ID,
                name="main user",
                email="main.user@example.com",
            )
            session.add(db_user)
            session.commit()


# flake8: noqa
def shell(db):
    if settings.environment not in ("develop", "local"):
        raise Exception("This script must be run in develop environment")
    from carbonserver.api.infra.database.sql_models import (
        Membership as SqlModelMembership,
    )
    from carbonserver.api.infra.database.sql_models import Project as SqlModelProject
    from carbonserver.api.infra.database.sql_models import User as SqlModelUser

    logger.info("Checking initial data...")
    with db.session() as session:
        import IPython

        IPython.embed()


def main() -> None:
    db = Database(db_url=settings.db_url)
    check_initial_data(db)


if __name__ == "__main__":
    main()
