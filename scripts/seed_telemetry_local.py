"""Seed local Postgres with the shared telemetry project, experiment, and API token."""

from __future__ import annotations

import sys
import uuid
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CARBONSERVER_ROOT = REPO_ROOT / "carbonserver"
sys.path[:0] = [str(CARBONSERVER_ROOT), str(REPO_ROOT)]

from carbonserver.api.infra.api_key_utils import generate_lookup_value, get_api_key_hash
from carbonserver.api.infra.database.sql_models import (
    Experiment,
    Organization,
    Project,
    ProjectToken,
)
from carbonserver.api.schemas import AccessLevel
from carbonserver.database.database import SessionLocal
from carbonserver.telemetry_defaults import (
    DEFAULT_TELEMETRY_API_KEY,
    DEFAULT_TELEMETRY_EXPERIMENT_ID,
)

TELEMETRY_ORG_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TELEMETRY_PROJECT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
TELEMETRY_TOKEN_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")


def seed_telemetry_local() -> None:
    """Insert telemetry org/project/experiment/token if missing."""
    experiment_id = uuid.UUID(DEFAULT_TELEMETRY_EXPERIMENT_ID)
    hashed_token = get_api_key_hash(DEFAULT_TELEMETRY_API_KEY)
    if isinstance(hashed_token, bytes):
        hashed_token = hashed_token.decode()

    with SessionLocal() as session:
        if session.get(Experiment, experiment_id) is not None:
            print("Telemetry experiment already seeded.")
            return

        session.merge(
            Organization(
                id=TELEMETRY_ORG_ID,
                name="CodeCarbon Telemetry",
                description="Local telemetry seed data",
            )
        )
        session.merge(
            Project(
                id=TELEMETRY_PROJECT_ID,
                name="Telemetry",
                description="Product telemetry",
                public=True,
                organization_id=TELEMETRY_ORG_ID,
            )
        )
        session.merge(
            Experiment(
                id=experiment_id,
                timestamp=datetime.utcnow(),
                name="Telemetry",
                description="Product telemetry experiment",
                project_id=TELEMETRY_PROJECT_ID,
            )
        )
        session.merge(
            ProjectToken(
                id=TELEMETRY_TOKEN_ID,
                project_id=TELEMETRY_PROJECT_ID,
                name="Telemetry default token",
                hashed_token=hashed_token,
                lookup_value=generate_lookup_value(DEFAULT_TELEMETRY_API_KEY),
                revoked=False,
                access=AccessLevel.READ_WRITE.value,
            )
        )
        session.commit()
        print("Seeded telemetry org/project/experiment/token for local API testing.")


if __name__ == "__main__":
    seed_telemetry_local()
