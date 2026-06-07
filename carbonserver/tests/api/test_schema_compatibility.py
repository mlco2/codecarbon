import dataclasses
import importlib.util
from pathlib import Path

import pytest

from carbonserver.api import schemas as server_schemas


def load_client_schemas():
    repo_root = Path(__file__).resolve().parents[3]
    client_schema_path = repo_root / "codecarbon" / "core" / "schemas.py"
    spec = importlib.util.spec_from_file_location(
        "codecarbon_client_schemas", client_schema_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


client_schemas = load_client_schemas()


CREATE_SCHEMA_PAIRS = [
    (client_schemas.EmissionCreate, server_schemas.EmissionCreate),
    (client_schemas.RunCreate, server_schemas.RunCreate),
    (client_schemas.ExperimentCreate, server_schemas.ExperimentCreate),
    (client_schemas.ProjectCreate, server_schemas.ProjectCreate),
    (client_schemas.OrganizationCreate, server_schemas.OrganizationCreate),
]


@pytest.mark.parametrize(("client_schema", "server_schema"), CREATE_SCHEMA_PAIRS)
def test_client_create_schemas_match_server_fields(client_schema, server_schema):
    client_fields = {field.name for field in dataclasses.fields(client_schema)}
    server_fields = set(server_schema.model_fields)

    assert client_fields == server_fields


@pytest.mark.parametrize(
    ("client_payload", "server_schema"),
    [
        (
            client_schemas.EmissionCreate(
                timestamp="2021-04-04T08:43:00+02:00",
                run_id="40088f1a-d28e-4980-8d80-bf5600056a14",
                duration=98745,
                emissions_sum=1544.54,
                emissions_rate=1.548444,
                cpu_power=0.3,
                gpu_power=0.0,
                ram_power=0.15,
                cpu_energy=55.21874,
                gpu_energy=0.0,
                ram_energy=2.0,
                energy_consumed=57.21874,
                cpu_utilization_percent=12.5,
                gpu_utilization_percent=34.5,
                ram_utilization_percent=56.5,
                wue=0.8,
            ),
            server_schemas.EmissionCreate,
        ),
        (
            client_schemas.RunCreate(
                timestamp="2021-04-04T08:43:00+02:00",
                experiment_id="8edb03e1-9a28-452a-9c93-a3b6560136d7",
                os="macOS-10.15.7-x86_64-i386-64bit",
                python_version="3.8.0",
                codecarbon_version="2.1.3",
                cpu_count=12,
                cpu_model="Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz",
                gpu_count=4,
                gpu_model="NVIDIA",
                longitude=-7.6174,
                latitude=33.5822,
                region="EUROPE",
                provider="AWS",
                ram_total_size=83948.22,
                tracking_mode="Machine",
            ),
            server_schemas.RunCreate,
        ),
        (
            client_schemas.ExperimentCreate(
                timestamp="2021-04-04T08:43:00+02:00",
                name="Run on AWS",
                description="AWS API for Code Carbon",
                country_name="France",
                country_iso_code="FRA",
                region="france",
                on_cloud=True,
                cloud_provider="aws",
                cloud_region="eu-west-1a",
                project_id="8edb03e1-9a28-452a-9c93-a3b6560136d7",
            ),
            server_schemas.ExperimentCreate,
        ),
        (
            client_schemas.ProjectCreate(
                name="API Code Carbon",
                description="API for Code Carbon",
                organization_id="8edb03e1-9a28-452a-9c93-a3b6560136d7",
            ),
            server_schemas.ProjectCreate,
        ),
        (
            client_schemas.OrganizationCreate(
                name="Code Carbon",
                description="Save the world, one run at a time.",
            ),
            server_schemas.OrganizationCreate,
        ),
    ],
)
def test_client_create_payloads_validate_against_server_schemas(
    client_payload, server_schema
):
    server_schema.model_validate(dataclasses.asdict(client_payload))
