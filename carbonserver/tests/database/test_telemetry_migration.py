"""Cover the ``add telemetry table`` migration against both a fresh database
and one carrying the pre-existing, ``create_all``-generated ``telemetry``
table (old, wide schema, see #1171)."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.compiler import compiles


# Production is Postgres-only; sqlite has no native UUID type, so teach it to
# render one as CHAR(32) purely so the "fresh table" path is exercisable here.
@compiles(PGUUID, "sqlite")
def _compile_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(32)"


MIGRATION_PATH = (
    Path(__file__).parents[2]
    / "carbonserver"
    / "database"
    / "alembic"
    / "versions"
    / "20260927_add_telemetry_table.py"
)


def _load_migration():
    spec = importlib.util.spec_from_file_location(
        "telemetry_migration_20260927", MIGRATION_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


OLD_TABLE_EXTRA_COLUMNS = {
    "longitude",
    "latitude",
    "python_executable_hash",
    "total_emissions_kg",
    "host_machine_hash",
}
NEW_ONLY_COLUMNS = {
    "cpu_architecture",
    "python_env_type",
    "codecarbon_install_method",
}


def _create_old_table(conn, module, skip_columns=()):
    """Build the full pre-existing, ``create_all``-generated old schema."""
    all_columns = ["id VARCHAR PRIMARY KEY"]
    for column in [*module.NEW_COLUMNS, *module.OLD_ONLY_COLUMNS]:
        if column.name in skip_columns:
            continue
        sql_type = "VARCHAR"
        if isinstance(column.type, (sa.Integer, sa.Float)):
            sql_type = "FLOAT" if isinstance(column.type, sa.Float) else "INTEGER"
        elif isinstance(column.type, sa.DateTime):
            sql_type = "DATETIME"
        elif isinstance(column.type, sa.Boolean):
            sql_type = "BOOLEAN"
        all_columns.append(f"{column.name} {sql_type}")
    conn.execute(sa.text(f"CREATE TABLE telemetry ({', '.join(all_columns)})"))
    conn.execute(
        sa.text(
            "INSERT INTO telemetry (id, timestamp, telemetry_level, os, "
            "longitude, latitude) VALUES "
            "('row-1', '2026-01-01 00:00:00', 'extensive', 'Linux', 1.0, 2.0)"
        )
    )


def test_timestamp_column_is_timezone_aware_on_create():
    """Naive timestamps are ambiguous across servers in different zones;
    the column must be created as ``timestamptz``."""
    module = _load_migration()
    (timestamp_column,) = [c for c in module.NEW_COLUMNS if c.name == "timestamp"]
    assert isinstance(timestamp_column.type, sa.DateTime)
    assert timestamp_column.type.timezone is True


def test_bind_is_postgres_helper():
    module = _load_migration()

    class _FakeDialect:
        def __init__(self, name):
            self.name = name

    class _FakeBind:
        def __init__(self, name):
            self.dialect = _FakeDialect(name)

    assert module._bind_is_postgres(_FakeBind("postgresql")) is True
    assert module._bind_is_postgres(_FakeBind("sqlite")) is False


def test_upgrade_alters_timestamp_to_timezone_aware_on_existing_postgres_table():
    """When the table pre-exists on Postgres, the migration must alter the
    ``timestamp`` column type to timestamptz rather than leaving it naive."""
    module = _load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        _create_old_table(conn, module)
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            with (
                patch.object(module, "_bind_is_postgres", return_value=True),
                patch("alembic.op.alter_column") as mock_alter,
                patch("alembic.op.create_index"),
                patch("alembic.op.execute"),
            ):
                module.upgrade()
    (call,) = mock_alter.call_args_list
    args, kwargs = call
    assert args == ("telemetry", "timestamp")
    assert kwargs["type_"].timezone is True
    assert kwargs["postgresql_using"] == "timestamp AT TIME ZONE 'UTC'"


def test_upgrade_creates_table_when_absent():
    module = _load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            module.upgrade()
        columns = {c["name"] for c in sa.inspect(conn).get_columns("telemetry")}
    assert "cpu_architecture" in columns
    assert not (columns & OLD_TABLE_EXTRA_COLUMNS)


def test_upgrade_migrates_pre_existing_old_schema_table_preserving_rows():
    module = _load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        _create_old_table(conn, module)
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            module.upgrade()
        columns = {c["name"] for c in sa.inspect(conn).get_columns("telemetry")}
        rows = conn.execute(sa.text("SELECT id, telemetry_level FROM telemetry")).all()
    assert NEW_ONLY_COLUMNS <= columns
    assert not (columns & OLD_TABLE_EXTRA_COLUMNS)
    # The pre-existing row survives the schema change untouched.
    assert rows == [("row-1", "extensive")]


def test_upgrade_adds_a_genuinely_missing_new_column():
    """Covers the "add any missing column" branch: an old table that lacks
    one of the new model's columns gets it added (nullable)."""
    module = _load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        _create_old_table(conn, module, skip_columns={"cpu_architecture"})
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            module.upgrade()
        columns = {c["name"] for c in sa.inspect(conn).get_columns("telemetry")}
    assert "cpu_architecture" in columns


def test_downgrade_alters_timestamp_back_to_naive_on_postgres():
    module = _load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        _create_old_table(conn, module)
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            module.upgrade()
            with (
                patch.object(module, "_bind_is_postgres", return_value=True),
                patch("alembic.op.alter_column") as mock_alter,
                patch("alembic.op.execute"),
            ):
                module.downgrade()
    (call,) = mock_alter.call_args_list
    args, kwargs = call
    assert args == ("telemetry", "timestamp")
    assert kwargs["type_"].timezone is False
    assert kwargs["postgresql_using"] == "timestamp AT TIME ZONE 'UTC'"


def test_ensure_retention_is_a_noop_on_sqlite():
    """SQLite has no plpgsql triggers; ``_ensure_retention`` must not touch
    the connection at all, and the migration must still succeed."""
    module = _load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            module.upgrade()  # must not raise
        indexes = {ix["name"] for ix in sa.inspect(conn).get_indexes("telemetry")}
    assert "ix_telemetry_timestamp" not in indexes


def test_upgrade_creates_retention_index_trigger_and_function_on_postgres():
    """On Postgres, upgrade must create the timestamp index, the purge
    function and the statement-level AFTER INSERT trigger."""
    module = _load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            with (
                patch.object(module, "_bind_is_postgres", return_value=True),
                patch("alembic.op.create_index") as mock_create_index,
                patch("alembic.op.execute") as mock_execute,
            ):
                module.upgrade()
    index_calls = [c.args for c in mock_create_index.call_args_list]
    assert ("ix_telemetry_timestamp", "telemetry", ["timestamp"]) in index_calls
    executed_sql = "\n".join(c.args[0] for c in mock_execute.call_args_list)
    assert "CREATE OR REPLACE FUNCTION telemetry_purge()" in executed_sql
    assert "DELETE FROM telemetry WHERE timestamp < now() - interval '3 years'" in (
        executed_sql
    )
    assert "CREATE TRIGGER telemetry_retention" in executed_sql
    assert "FOR EACH STATEMENT" in executed_sql


def test_downgrade_drops_retention_trigger_function_and_index_on_postgres():
    module = _load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        _create_old_table(conn, module)
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            module.upgrade()
            with (
                patch.object(module, "_bind_is_postgres", return_value=True),
                patch("alembic.op.alter_column"),
                patch("alembic.op.execute") as mock_execute,
            ):
                module.downgrade()
    executed_sql = "\n".join(c.args[0] for c in mock_execute.call_args_list)
    assert "DROP TRIGGER IF EXISTS telemetry_retention" in executed_sql
    assert "DROP FUNCTION IF EXISTS telemetry_purge()" in executed_sql
    assert "DROP INDEX IF EXISTS ix_telemetry_timestamp" in executed_sql


def test_downgrade_restores_old_columns_as_nullable_preserving_rows():
    module = _load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        _create_old_table(conn, module)
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            module.upgrade()
            module.downgrade()
        columns = {c["name"] for c in sa.inspect(conn).get_columns("telemetry")}
        rows = conn.execute(sa.text("SELECT id FROM telemetry")).all()
    assert OLD_TABLE_EXTRA_COLUMNS <= columns
    assert rows == [("row-1",)]
