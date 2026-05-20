"""Test to ensure that the telemetry schema used by the CarbonServer API does not drift from the core telemetry schema defined in CodeCarbon."""

import importlib.util
from copy import deepcopy
from pathlib import Path

from carbonserver.api.schemas_telemetry import TelemetryCreate as ServerTelemetryCreate

REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_TELEMETRY_SCHEMA_PATH = (
    REPO_ROOT / "codecarbon" / "core" / "telemetry" / "schemas.py"
)


def _load_core_telemetry_create():
    spec = importlib.util.spec_from_file_location(
        "core_telemetry_schemas",
        CORE_TELEMETRY_SCHEMA_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.TelemetryCreate


def _contract_schema(schema):
    contract = deepcopy(schema)
    contract.pop("description", None)
    contract.pop("example", None)
    contract.pop("examples", None)
    contract.pop("title", None)
    contract.pop("$defs", None)

    for property_schema in contract.get("properties", {}).values():
        property_schema.pop("description", None)
        property_schema.pop("example", None)
        property_schema.pop("examples", None)
        property_schema.pop("title", None)

    return contract


def test_core_and_server_telemetry_schemas_do_not_drift():
    CoreTelemetryCreate = _load_core_telemetry_create()

    assert _contract_schema(
        CoreTelemetryCreate.model_json_schema()
    ) == _contract_schema(ServerTelemetryCreate.model_json_schema())
