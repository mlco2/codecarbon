"""
Test that client (codecarbon/core/schemas.py) and server
(carbonserver/carbonserver/api/schemas.py) schemas are compatible.

A mismatch between these schemas can cause silent data corruption or API errors.
This test was added to prevent regressions like the one fixed in PR #1189,
where `on_cloud` was typed as `str` on one side and `bool` on the other.

Related issue: https://github.com/mlco2/codecarbon/issues/1190
"""
import ast
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
CLIENT_SCHEMA_PATH = REPO_ROOT / "codecarbon" / "core" / "schemas.py"
SERVER_SCHEMA_PATH = REPO_ROOT / "carbonserver" / "carbonserver" / "api" / "schemas.py"


# ---------------------------------------------------------------------------
# AST helpers - parse schema files without importing them
# ---------------------------------------------------------------------------


def _is_pydantic_required_field(value_node: ast.expr) -> bool:
    """
    Return True when the node marks a Pydantic field as required.

    Covers two cases:
    - Field(...)  -- the classic explicit-required sentinel.
    - Field()     -- bare call with no positional arg and no default
                     or default_factory keyword; Pydantic v2 treats
                     this as required.
    """
    if not isinstance(value_node, ast.Call):
        return False
    func = value_node.func
    func_name = (
        func.id
        if isinstance(func, ast.Name)
        else (func.attr if isinstance(func, ast.Attribute) else "")
    )
    if func_name != "Field":
        return False

    # Field(...) - Ellipsis as first positional argument
    if (
        value_node.args
        and isinstance(value_node.args[0], ast.Constant)
        and value_node.args[0].value is ...
    ):
        return True

    # Bare Field() - no positional args, no default/default_factory keyword
    if not value_node.args:
        kw_names = {kw.arg for kw in value_node.keywords}
        if "default" not in kw_names and "default_factory" not in kw_names:
            return True

    return False


def _parse_class_fields(filepath: Path, class_name: str) -> dict[str, dict]:
    """
    Parse filepath with the ast module and return a dict of annotated fields
    declared directly on class_name:

        {
            "field_name": {
                "annotation": "Optional[bool]",
                "required": True | False,
            },
            ...
        }

    Works for both plain Python dataclasses and Pydantic BaseModel subclasses.
    Un-annotated class-level assignments (e.g. model_config = ...) are
    intentionally ignored.
    """
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            fields: dict[str, dict] = {}
            for item in node.body:
                if not (
                    isinstance(item, ast.AnnAssign)
                    and isinstance(item.target, ast.Name)
                ):
                    continue

                field_name = item.target.id
                annotation = ast.unparse(item.annotation)

                # A field is required when:
                # 1. It has no right-hand side at all (pure annotation)
                # 2. Its right-hand side is a Pydantic required-field marker
                if item.value is None or _is_pydantic_required_field(item.value):
                    required = True
                else:
                    required = False

                fields[field_name] = {"annotation": annotation, "required": required}
            return fields

    return {}  # class not found - tests that call this will get empty dicts


# ---------------------------------------------------------------------------
# Type-compatibility helpers
# ---------------------------------------------------------------------------


def _unwrap_optional(annotation: str) -> str:
    """
    Strip an Optional / Union-with-None wrapper to return the core type.

    Handles all three common spellings:
    - Optional[X]      -> X
    - X | None         -> X   (PEP 604 union syntax)
    - Union[X, None]   -> X

    Any annotation that is not a nullable wrapper is returned unchanged.
    """
    # Optional[X]
    if annotation.startswith("Optional[") and annotation.endswith("]"):
        return annotation[len("Optional["):-1]

    # X | None  or  None | X
    if "|" in annotation:
        parts = [p.strip() for p in annotation.split("|")]
        non_none = [p for p in parts if p != "None"]
        if len(non_none) == 1:
            return non_none[0]

    # Union[X, None]  or  Union[None, X]
    if annotation.startswith("Union[") and annotation.endswith("]"):
        inner = annotation[len("Union["):-1]
        parts = [p.strip() for p in inner.split(",")]
        non_none = [p for p in parts if p != "None"]
        if len(non_none) == 1:
            return non_none[0]

    return annotation


# Pydantic coerces these client-side types to the server-side types at
# validation time, so they are considered wire-compatible.
# Key  = client core type (after unwrapping Optional)
# Value = set of acceptable server core types (after unwrapping Optional)
_COMPATIBLE_CORE_TYPES: dict[str, set[str]] = {
    # The client uses plain str for UUIDs and datetime strings;
    # Pydantic on the server will parse those correctly.
    "str": {"str", "UUID", "datetime"},
    "UUID": {"UUID", "str"},
    "datetime": {"datetime", "str"},
    # Scalar types must match exactly.
    "bool": {"bool"},
    "int": {"int"},
    "float": {"float"},
}


def _types_compatible(client_annotation: str, server_annotation: str) -> bool:
    """
    Return True when client_annotation is safe to send to an endpoint
    that expects server_annotation.

    Optional wrappers are stripped before comparison so that, for example,
    bool (client) and Optional[bool] (server) are treated as compatible --
    the server simply allows None in addition to a bool value.

    A bool vs str mismatch (the bug fixed in #1189) returns False.
    """
    if client_annotation == server_annotation:
        return True

    client_core = _unwrap_optional(client_annotation)
    server_core = _unwrap_optional(server_annotation)

    if client_core == server_core:
        return True

    return server_core in _COMPATIBLE_CORE_TYPES.get(client_core, set())


# ---------------------------------------------------------------------------
# Schema pairs under test
#
# Each entry is (label, client_class_name, server_class_name).
# The client and server classes share the same names today; the three-tuple
# structure is intentional so that if the server classes are ever renamed
# (e.g. EmissionBase -> EmissionRead) only this list needs updating, not the
# test functions themselves.
# ---------------------------------------------------------------------------
SCHEMA_PAIRS = [
    ("EmissionBase", "EmissionBase", "EmissionBase"),
    ("RunBase", "RunBase", "RunBase"),
    ("ExperimentBase", "ExperimentBase", "ExperimentBase"),
    ("ProjectBase", "ProjectBase", "ProjectBase"),
    ("OrganizationBase", "OrganizationBase", "OrganizationBase"),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("label,client_cls,server_cls", SCHEMA_PAIRS)
def test_client_fields_exist_in_server(label: str, client_cls: str, server_cls: str):
    """
    Every field declared in the client schema must also exist in the server
    schema. If the server drops a field the client sends, the payload will
    be silently ignored or rejected.
    """
    client_fields = _parse_class_fields(CLIENT_SCHEMA_PATH, client_cls)
    server_fields = _parse_class_fields(SERVER_SCHEMA_PATH, server_cls)

    assert client_fields, f"[{label}] Could not parse client class '{client_cls}'"
    assert server_fields, f"[{label}] Could not parse server class '{server_cls}'"

    missing = set(client_fields) - set(server_fields)
    assert not missing, (
        f"[{label}] Fields present in client but missing from server schema: {missing}\n"
        f"  client : {CLIENT_SCHEMA_PATH.relative_to(REPO_ROOT)}\n"
        f"  server : {SERVER_SCHEMA_PATH.relative_to(REPO_ROOT)}"
    )


@pytest.mark.parametrize("label,client_cls,server_cls", SCHEMA_PAIRS)
def test_required_server_fields_exist_in_client(
    label: str, client_cls: str, server_cls: str
):
    """
    Every required server field (one without a default value) must also
    appear in the client schema. If the client never sends a required field,
    every API call for that resource will fail validation.
    """
    client_fields = _parse_class_fields(CLIENT_SCHEMA_PATH, client_cls)
    server_fields = _parse_class_fields(SERVER_SCHEMA_PATH, server_cls)

    assert client_fields, f"[{label}] Could not parse client class '{client_cls}'"
    assert server_fields, f"[{label}] Could not parse server class '{server_cls}'"

    required_server_fields = {
        name for name, meta in server_fields.items() if meta["required"]
    }
    missing = required_server_fields - set(client_fields)
    assert not missing, (
        f"[{label}] Required server fields missing from client schema: {missing}\n"
        f"  client : {CLIENT_SCHEMA_PATH.relative_to(REPO_ROOT)}\n"
        f"  server : {SERVER_SCHEMA_PATH.relative_to(REPO_ROOT)}"
    )


@pytest.mark.parametrize("label,client_cls,server_cls", SCHEMA_PAIRS)
def test_shared_field_types_are_compatible(
    label: str, client_cls: str, server_cls: str
):
    """
    For every field that appears in both schemas, the client-side type must
    be wire-compatible with the server-side type.

    This test would have caught the on_cloud: str (server) vs
    on_cloud: bool (client) mismatch that was fixed in PR #1189.
    """
    client_fields = _parse_class_fields(CLIENT_SCHEMA_PATH, client_cls)
    server_fields = _parse_class_fields(SERVER_SCHEMA_PATH, server_cls)

    assert client_fields, f"[{label}] Could not parse client class '{client_cls}'"
    assert server_fields, f"[{label}] Could not parse server class '{server_cls}'"

    shared = set(client_fields) & set(server_fields)
    mismatches: list[str] = []

    for field in sorted(shared):
        c_type = client_fields[field]["annotation"]
        s_type = server_fields[field]["annotation"]
        if not _types_compatible(c_type, s_type):
            mismatches.append(f"  {field}: client={c_type!r}  server={s_type!r}")

    assert not mismatches, (
        f"[{label}] Incompatible types between client and server schemas:\n"
        + "\n".join(mismatches)
        + f"\n  client : {CLIENT_SCHEMA_PATH.relative_to(REPO_ROOT)}"
        + f"\n  server : {SERVER_SCHEMA_PATH.relative_to(REPO_ROOT)}"
    )


@pytest.mark.parametrize("label,client_cls,server_cls", SCHEMA_PAIRS)
def test_required_alignment_on_shared_fields(
    label: str, client_cls: str, server_cls: str
):
    """
    If a server field is required, the client must not treat it as optional.

    When the client marks a field Optional (or gives it a default of None)
    but the server requires a value, the client can legally send None and
    the server will reject it -- the same class of silent wire mismatch as
    the type bug fixed in #1189, just on the optionality axis.
    """
    client_fields = _parse_class_fields(CLIENT_SCHEMA_PATH, client_cls)
    server_fields = _parse_class_fields(SERVER_SCHEMA_PATH, server_cls)

    assert client_fields, f"[{label}] Could not parse client class '{client_cls}'"
    assert server_fields, f"[{label}] Could not parse server class '{server_cls}'"

    weakened = [
        f
        for f in set(client_fields) & set(server_fields)
        if server_fields[f]["required"] and not client_fields[f]["required"]
    ]
    assert not weakened, (
        f"[{label}] server requires fields client treats as optional: {weakened}\n"
        f"  client : {CLIENT_SCHEMA_PATH.relative_to(REPO_ROOT)}\n"
        f"  server : {SERVER_SCHEMA_PATH.relative_to(REPO_ROOT)}"
    )
