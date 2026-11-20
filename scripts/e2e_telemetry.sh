#!/usr/bin/env bash
# End-to-end telemetry check against a throwaway Postgres and a local API.
#
# 1. Starts the docker-compose Postgres under its own project name, so the
#    volume is separate from your dev database, and migrates it.
# 2. Runs the API with uvicorn on http://localhost:8008.
# 3. Runs one library process (two tracker stops) and one `codecarbon monitor`
#    process with telemetry at `minimal`, both pointed at that API.
# 4. Checks the database: one row per process, only allowed columns.
# Everything is torn down on exit.
#
# Set E2E_ALLOW_PULL=1 to allow pulling the postgres image when it is missing.
# Set E2E_PG_PORT to change the host port for Postgres (default 55432, so a dev
# database already on 5432 does not clash).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT=codecarbon-e2e
API_URL=http://localhost:8008
PG_PORT="${E2E_PG_PORT:-55432}"
export DATABASE_URL="postgresql://codecarbon-user:supersecret@localhost:${PG_PORT}/codecarbon_db"
WORK="$(mktemp -d)"
cat >"$WORK/compose.override.yml" <<YAML
services:
  postgres:
    ports: !override
      - "${PG_PORT}:5432"
YAML
COMPOSE=(docker compose -f "$ROOT/docker-compose.yml" -f "$WORK/compose.override.yml" -p "$PROJECT")
API_PID=""

cleanup() {
    if [ -n "$API_PID" ]; then
        kill "$API_PID" 2>/dev/null || echo "WARN: API process already gone" >&2
    fi
    if ! "${COMPOSE[@]}" down -v; then
        echo "WARN: docker compose down failed; remove project $PROJECT by hand" >&2
    fi
    rm -rf "$WORK"
}

if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon is not reachable." >&2
    exit 1
fi
if [ -z "$(docker image ls -q postgres)" ] && [ "${E2E_ALLOW_PULL:-0}" != 1 ]; then
    echo "ERROR: no postgres image present; pulling one downloads about 150 MB." >&2
    echo "Re-run with E2E_ALLOW_PULL=1 to allow it." >&2
    exit 2
fi
trap cleanup EXIT

echo "== Starting Postgres"
"${COMPOSE[@]}" up -d postgres
pg_ready=0
for _ in $(seq 1 30); do
    if "${COMPOSE[@]}" exec -T postgres \
        pg_isready -U codecarbon-user -d codecarbon_db >/dev/null 2>&1; then
        pg_ready=1
        break
    fi
    sleep 1
done
if [ "$pg_ready" -ne 1 ]; then
    echo "ERROR: Postgres never became ready (pg_isready kept failing)." >&2
    exit 1
fi

echo "== Migrating"
(cd "$ROOT/carbonserver" && uv run --project . python -m alembic \
    -c carbonserver/database/alembic.ini upgrade head)

if curl --noproxy '*' -fsS "$API_URL/" >/dev/null 2>&1; then
    echo "ERROR: something is already listening on $API_URL before the API starts." >&2
    exit 1
fi

echo "== Starting API"
(cd "$ROOT/carbonserver" && exec env AUTH_PROVIDER=none ENVIRONMENT=local \
    uv run --project . uvicorn main:app --port 8008 >"$WORK/api.log" 2>&1) &
API_PID=$!
api_up=0
for _ in $(seq 1 60); do
    if ! kill -0 "$API_PID" 2>/dev/null; then
        echo "ERROR: API process exited before coming up; log follows" >&2
        cat "$WORK/api.log" >&2
        exit 1
    fi
    if curl --noproxy '*' -fsS "$API_URL/" >/dev/null 2>&1; then
        api_up=1
        break
    fi
    sleep 1
done
if [ "$api_up" -ne 1 ] || ! kill -0 "$API_PID" 2>/dev/null; then
    echo "ERROR: API did not come up; log follows" >&2
    cat "$WORK/api.log" >&2
    exit 1
fi

export CODECARBON_TELEMETRY_API_URL="$API_URL"
export CODECARBON_TELEMETRY_LEVEL=minimal
export CODECARBON_ALLOW_MULTIPLE_RUNS=True
export NO_PROXY="localhost,127.0.0.1"
cd "$WORK"

echo "== Library process: two stops, expect one row"
uv run --project "$ROOT" python - <<'PY'
import time

from codecarbon import EmissionsTracker

for _ in range(2):
    tracker = EmissionsTracker(save_to_file=False, save_to_api=False)
    tracker.start()
    time.sleep(2)
    tracker.stop()
PY

echo "== CLI monitor process: expect one row"
uv run --project "$ROOT" codecarbon monitor --no-api --telemetry-level minimal \
    -- python -c "import time; time.sleep(2)"

echo "== Checking the database"
(cd "$ROOT/carbonserver" && TELEMETRY_E2E_EXPECTED_ROWS=2 \
    uv run --project . --extra dev python -m pytest -q -s -p no:cacheprovider \
    tests/api/integration/test_telemetry_e2e_db.py)
