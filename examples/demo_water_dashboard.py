#!/usr/bin/env python3
"""
Demo helper for the water dashboard feature.

Recommended usage from repo root:

    python examples/demo_water_dashboard.py demo --duration 60

What it does:
    1) Patches a few LOCAL DEV files needed to run the stack on localhost
       (with automatic backups so they can be restored later)
    2) Runs `docker compose up -d --build` (takes up most of the execution time)
    3) Seeds one PUBLIC demo organization/project/experiment into Postgres
    4) Generates a valid project token in the DB
    5) Runs a real CodeCarbon workload locally and uploads it to the local API
    6) Verifies that water_consumed is non-zero via the backend API
    7) Prints the public project URL to open in the browser

When done, restore the local files and remove the demo DB rows with:

    python examples/demo_water_dashboard.py cleanup

Notes:
    - This script is meant for local demo/review only.
    - It is deliberately separate from the actual feature code so the feature branch
      can stay clean.
    - It uses the PUBLIC project page, so it does not depend on sign-in.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / ".demo_water_dashboard_backups"
COMPOSE_OVERRIDE = ROOT / ".demo_water_dashboard.compose.override.yml"


# Deterministic demo objects
DEMO_ORG_ID = "90000000-0000-0000-0000-000000000001"
DEMO_PROJECT_ID = "90000000-0000-0000-0000-000000000002"
DEMO_EXPERIMENT_ID = "90000000-0000-0000-0000-000000000003"
DEMO_TOKEN_ROW_ID = "90000000-0000-0000-0000-000000000004"

DEMO_ORG_NAME = "Water Dashboard Demo Org"
DEMO_PROJECT_NAME = "Water Dashboard Demo Project"
DEMO_EXPERIMENT_NAME = "Water Dashboard Demo Experiment"
DEMO_TOKEN_NAME = "Water Dashboard Demo Token"

DEMO_PROJECT_ENCRYPTION_KEY = "demo-water-dashboard-key-32chars"

DEMO_TOKEN_PLAINTEXT = "cpt_demo_water_dashboard_001"

API_BASE = "http://localhost:8000"

LOCAL_PATCH_FILES = [
    ROOT / "webapp/.env.development",
    ROOT / "webapp/dev.Dockerfile",
    ROOT / "carbonserver/docker/Dockerfile",
    ROOT / "carbonserver/docker/entrypoint.sh",
]


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        text=True,
        capture_output=capture,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n\n"
            f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )
    return result


def info(msg: str) -> None:
    print(f"[demo] {msg}")


def backup_file(path: Path) -> None:
    rel = path.relative_to(ROOT)
    backup_path = BACKUP_DIR / rel
    if not backup_path.exists():
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)


def restore_file(path: Path) -> None:
    rel = path.relative_to(ROOT)
    backup_path = BACKUP_DIR / rel
    if backup_path.exists():
        shutil.copy2(backup_path, path)


def generate_public_project_link(project_id: str) -> str:
    js = rf"""
const crypto = require("crypto");
const projectId = "{project_id}";
const secret = "{DEMO_PROJECT_ENCRYPTION_KEY}";
const hmac = crypto.createHmac("sha256", secret);
hmac.update(projectId);
const iv = Buffer.from(hmac.digest().subarray(0, 16));
const key = Buffer.from(secret.substring(0, 32).padEnd(32, "0"));
const cipher = crypto.createCipheriv("aes-256-cbc", key, iv);
let encrypted = cipher.update(projectId, "utf8", "base64");
encrypted += cipher.final("base64");
const combined = Buffer.concat([iv, Buffer.from(encrypted, "base64")]);
console.log(combined.toString("base64url"));
"""
    result = run(
        ["docker", "compose", "exec", "-T", "ui", "node", "-e", js],
        check=True,
        capture=True,
    )
    encrypted_id = result.stdout.strip()
    return f"http://localhost:3000/public/projects/{encrypted_id}"



def write_compose_override() -> None:
    COMPOSE_OVERRIDE.write_text(
        """services:
  carbonserver:
    ports:
      - "8000:8000"
  ui:
    ports:
      - "3000:3000"
  postgres:
    ports:
      - "5480:5432"
""",
        encoding="utf-8",
        newline="\n",
    )


def remove_compose_override_if_any() -> None:
    if COMPOSE_OVERRIDE.exists():
        COMPOSE_OVERRIDE.unlink()


def patch_env_development() -> None:
    path = ROOT / "webapp/.env.development"
    backup_file(path)
    text = path.read_text(encoding="utf-8")

    replacements = {
        "NEXT_PUBLIC_BASE_URL": "http://localhost:3000",
        "NEXT_PUBLIC_API_URL": "http://localhost:8000",
        "FIEF_BASE_URL": "http://localhost:8000",
        "PROJECT_ENCRYPTION_KEY": DEMO_PROJECT_ENCRYPTION_KEY,
    }

    lines = text.splitlines()
    seen = set()
    out = []
    for line in lines:
        replaced = False
        for key, value in replacements.items():
            if line.startswith(f"{key}="):
                out.append(f"{key}={value}")
                seen.add(key)
                replaced = True
                break
        if not replaced:
            out.append(line)

    for key, value in replacements.items():
        if key not in seen:
            out.append(f"{key}={value}")

    path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def patch_webapp_dockerfile() -> None:
    path = ROOT / "webapp/dev.Dockerfile"
    backup_file(path)
    text = path.read_text(encoding="utf-8")

    # Force Node 20 for yarn deps that now require it
    text = re.sub(r"FROM\s+node:\d+[^\s]*", "FROM node:20", text, count=1)

    path.write_text(text, encoding="utf-8", newline="\n")


def patch_carbonserver_dockerfile() -> None:
    path = ROOT / "carbonserver/docker/Dockerfile"
    backup_file(path)
    text = path.read_text(encoding="utf-8")

    old = 'RUN uv pip install --system -e ".[api]"'
    new = 'RUN UV_HTTP_TIMEOUT=180 uv pip install --system -e ".[api]"'
    text = text.replace(old, new)

    path.write_text(text, encoding="utf-8", newline="\n")


def normalize_entrypoint() -> None:
    path = ROOT / "carbonserver/docker/entrypoint.sh"
    backup_file(path)
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    path.write_text(text, encoding="utf-8", newline="\n")


def patch_local_dev_files() -> None:
    info("Patching local dev files (with backups)")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    patch_env_development()
    patch_webapp_dockerfile()
    patch_carbonserver_dockerfile()
    normalize_entrypoint()


def restore_local_dev_files() -> None:
    info("Restoring patched local dev files from backups")
    for path in LOCAL_PATCH_FILES:
        restore_file(path)


def docker_compose_up() -> None:
    info("Starting local stack with docker compose")
    write_compose_override()
    run(
        [
            "docker",
            "compose",
            "-f",
            "docker-compose.yml",
            "-f",
            ".demo_water_dashboard.compose.override.yml",
            "up",
            "-d",
            "--build",
        ],
        check=True,
        capture=True,
    )

def wait_for_url(url: str, timeout_sec: int = 300) -> None:
    info(f"Waiting for {url}")
    deadline = time.time() + timeout_sec
    last_error = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if 200 <= resp.status < 500:
                    return
        except urllib.error.HTTPError as exc:
            if 200 <= exc.code < 500:
                return
            last_error = exc
        except Exception as exc:
            last_error = exc
        time.sleep(2)
    raise RuntimeError(f"Timed out waiting for {url}. Last error: {last_error}")


def psql(sql: str) -> str:
    result = run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "codecarbon-user",
            "-d",
            "codecarbon_db",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ],
        check=True,
        capture=True,
    )
    return result.stdout.strip()


def generate_token_hash_in_container(token: str) -> str:
    cmd = (
        "import bcrypt; "
        f"token={token!r}; "
        "print(bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode())"
    )
    result = run(
        ["docker", "compose", "exec", "-T", "carbonserver", "python", "-c", cmd],
        check=True,
        capture=True,
    )
    return result.stdout.strip()


def seed_demo_data() -> None:
    info("Seeding demo organization / project / experiment / token")
    token_lookup = hashlib.sha256(DEMO_TOKEN_PLAINTEXT.encode()).hexdigest()[:8]
    token_hash = generate_token_hash_in_container(DEMO_TOKEN_PLAINTEXT)

    # org
    psql(
        f"""
        INSERT INTO organizations (id, name, description)
        VALUES ('{DEMO_ORG_ID}', '{DEMO_ORG_NAME}', 'Public demo org for the water dashboard')
        ON CONFLICT (id) DO UPDATE
        SET name = EXCLUDED.name,
            description = EXCLUDED.description;
        """
    )

    # project (public)
    psql(
        f"""
        INSERT INTO projects (id, name, description, organization_id, public)
        VALUES ('{DEMO_PROJECT_ID}', '{DEMO_PROJECT_NAME}', 'Public demo project for the water dashboard', '{DEMO_ORG_ID}', true)
        ON CONFLICT (id) DO UPDATE
        SET name = EXCLUDED.name,
            description = EXCLUDED.description,
            organization_id = EXCLUDED.organization_id,
            public = EXCLUDED.public;
        """
    )

    # experiment
    psql(
        f"""
        INSERT INTO experiments (
            id, timestamp, name, description, country_name, country_iso_code,
            region, on_cloud, cloud_provider, cloud_region, project_id
        )
        VALUES (
            '{DEMO_EXPERIMENT_ID}', NOW(), '{DEMO_EXPERIMENT_NAME}', 'Public demo experiment',
            'France', 'FRA', NULL, false, NULL, NULL, '{DEMO_PROJECT_ID}'
        )
        ON CONFLICT (id) DO UPDATE
        SET timestamp = NOW(),
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            country_name = EXCLUDED.country_name,
            country_iso_code = EXCLUDED.country_iso_code,
            on_cloud = EXCLUDED.on_cloud,
            cloud_provider = EXCLUDED.cloud_provider,
            cloud_region = EXCLUDED.cloud_region,
            project_id = EXCLUDED.project_id;
        """
    )

    # token
    psql(
        f"""
        INSERT INTO project_tokens (
            id, project_id, name, access, hashed_token, lookup_value, revoked
        )
        VALUES (
            '{DEMO_TOKEN_ROW_ID}', '{DEMO_PROJECT_ID}', '{DEMO_TOKEN_NAME}',
            2, '{token_hash}', '{token_lookup}', false
        )
        ON CONFLICT (id) DO UPDATE
        SET project_id = EXCLUDED.project_id,
            name = EXCLUDED.name,
            access = EXCLUDED.access,
            hashed_token = EXCLUDED.hashed_token,
            lookup_value = EXCLUDED.lookup_value,
            revoked = EXCLUDED.revoked;
        """
    )

    psql("UPDATE organizations SET description = '' WHERE description IS NULL;")
    psql("UPDATE projects SET description = '' WHERE description IS NULL;")
    psql("UPDATE experiments SET description = '' WHERE description IS NULL;")
    psql("UPDATE experiments SET timestamp = NOW() WHERE timestamp IS NULL;")


def ensure_repo_importable() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))


def run_demo_tracker(duration_sec: int) -> None:
    info(f"Running local tracked workload for {duration_sec} seconds")
    ensure_repo_importable()

    from codecarbon import EmissionsTracker  # local repo package

    tracker = EmissionsTracker(
        api_endpoint=API_BASE,
        save_to_api=True,
        save_to_file=False,
        experiment_id=DEMO_EXPERIMENT_ID,
        api_key=DEMO_TOKEN_PLAINTEXT,
    )

    tracker.start()
    end = time.time() + duration_sec
    x = 0
    while time.time() < end:
        x = (x + 1) % 1_000_000
    tracker.stop()


def http_get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} on {url}\n{body}") from exc


def verify_demo_data() -> dict:
    info("Verifying that the backend sees non-zero water_consumed")
    url = (
        f"{API_BASE}/projects/{DEMO_PROJECT_ID}/experiments/sums"
        f"?start_date=2000-01-01T00:00:00&end_date=2100-01-01T00:00:00"
    )
    data = http_get_json(url)
    if not data:
        raise RuntimeError("Project sums endpoint returned no data")

    row = data[0]
    water = row.get("water_consumed", 0)
    energy = row.get("energy_consumed", 0)
    emissions = row.get("emissions", 0)

    if water is None or water <= 0:
        raise RuntimeError(f"water_consumed is not > 0 in backend response: {row}")

    info(
        "Verification OK: "
        f"energy_consumed={energy}, water_consumed={water}, emissions={emissions}"
    )
    return row


def cleanup_demo_data() -> None:
    info("Removing demo DB rows")
    psql(f"DELETE FROM project_tokens WHERE project_id = '{DEMO_PROJECT_ID}';")
    psql(f"DELETE FROM runs WHERE experiment_id = '{DEMO_EXPERIMENT_ID}';")
    psql(f"DELETE FROM experiments WHERE id = '{DEMO_EXPERIMENT_ID}';")
    psql(f"DELETE FROM projects WHERE id = '{DEMO_PROJECT_ID}';")
    psql(f"DELETE FROM organizations WHERE id = '{DEMO_ORG_ID}';")


def remove_backups_if_any() -> None:
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)


def do_demo(duration_sec: int) -> None:
    patch_local_dev_files()
    docker_compose_up()

    wait_for_url(f"{API_BASE}/docs", timeout_sec=300)
    wait_for_url("http://localhost:3000", timeout_sec=300)

    seed_demo_data()
    run_demo_tracker(duration_sec)
    row = verify_demo_data()
    public_project_url = generate_public_project_link(DEMO_PROJECT_ID)
    print()
    print("=" * 72)
    print("Water dashboard demo is ready.")
    print()
    print(f"Open this URL in your browser:\n  {public_project_url}")
    print()
    print("Backend verification values:")
    print(json.dumps(row, indent=2))
    print("=" * 72)
    print()
    print("When finished, restore local files and remove demo DB rows with:")
    print("  python examples/demo_water_dashboard.py cleanup")


def do_cleanup() -> None:
    try:
        cleanup_demo_data()
    except Exception as exc:
        info(f"DB cleanup skipped or failed: {exc}")

    restore_local_dev_files()
    remove_backups_if_any()
    remove_compose_override_if_any()

    print()
    print("Cleanup complete.")
    print("If you want the running containers to reflect the restored files, run:")
    print("  docker compose up -d --build")
    print("The temporary compose override file was removed automatically.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Local water dashboard demo helper")
    sub = parser.add_subparsers(dest="command", required=True)

    demo_p = sub.add_parser("demo", help="Patch local files, build stack, seed demo data, run tracker")
    demo_p.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Tracked workload duration in seconds (default: 60). Use 300 for a more visible demo.",
    )

    sub.add_parser("cleanup", help="Restore patched files and delete demo DB rows")

    args = parser.parse_args()

    os.chdir(ROOT)

    if args.command == "demo":
        do_demo(args.duration)
    elif args.command == "cleanup":
        do_cleanup()
    else:
        parser.error("Unknown command")


if __name__ == "__main__":
    main()