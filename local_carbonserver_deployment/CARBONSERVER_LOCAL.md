# Carbonserver — Local & Production Deployment

Runs the CodeCarbon API server (`carbonserver`) backed by the shared postgres instance on `red-base-network`.  
No separate postgres container is needed: the server joins `red-base-network` where the shared `db` container (from `ecodev-infra`) already lives.

---

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin v2+)
- Shared postgres container running on `red-base-network` (`ecodev-infra`)
- **Local only:** `red-base-network` must exist locally — create it once if needed:
  ```bash
  docker network create red-base-network
  ```

---

## Environment setup

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Required variables in `.env`:

```dotenv
# Shared postgres (ecodev-infra db container on app-network)
db_host=db
db_port=5432
db_name=codecarbon_db
db_username=<postgres-user>
db_password=<postgres-password>

# Carbonserver public hostname (production only)
api_url=codecarbon-api.yourdomain.com

# Optional — override if your infra uses different network names
app_network=red-base-network
db_network=app-network
CODECARBON_LOG_LEVEL=INFO
```

---

## Local deployment

Starts the server on `http://localhost:8000` with hot-reload, using the shared postgres on `red-base-network`.

```bash
docker compose -f docker-compose.carbonserver.yml -f docker-compose.carbonserver.override.yml up -d --build
```

Verify the server is up:

```bash
curl http://localhost:8000/docs
```

The Swagger UI at `http://localhost:8000/docs` can be used to create the data model hierarchy needed before sending emissions.

To stop:

```bash
docker compose -f docker-compose.carbonserver.yml -f docker-compose.carbonserver.override.yml down
```

---

## Production deployment

Requires Traefik, `traefik-network`, `red-base-network`, and the shared postgres container to all be running.

```bash
docker compose -f docker-compose.carbonserver.yml up -d --build
```

The API will be available at `https://<api_url>` (HTTPS via Traefik + Let's Encrypt).

To stop:

```bash
docker compose -f docker-compose.carbonserver.yml down
```

---

## Bootstrap: create org → project → experiment → API token

Management endpoints require a Bearer JWT. In local (`ENVIRONMENT=develop`) mode the signature is **not** verified — any well-formed JWT with `sub` and `email` claims is accepted. Use the snippet below to generate one and register your user, then authenticate in Swagger.

### 1. Generate a local JWT and register your user

Run this once from any Python environment with `pyjwt` installed (`pip install pyjwt`):

```python
import uuid, jwt, datetime, requests

payload = {
    "sub": str(uuid.uuid4()),  # must be a UUID string
    "email": "admin@local.dev",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=365),
}
token = jwt.encode(payload, "dev-secret-key-change-in-production", algorithm="HS256")
print("sub (user id):", payload["sub"])
print("Bearer token:", token)

# Register the user (creates default org + project automatically)
resp = requests.get(
    "http://localhost:8000/auth/check",
    headers={"Authorization": f"Bearer {token}"},
)
print(resp.json())
```

> Keep note of the printed `sub` UUID — it is your user id in the database.

Copy the printed token — you will need it for all subsequent Swagger calls.

> The `JWT_KEY` in the override defaults to `dev-secret-key-change-in-production`. Set a custom value via `JWT_KEY=...` in `.env` and use it in the snippet above if you changed it.

### 2. Authenticate in Swagger UI

1. Open `http://localhost:8000/docs`
2. Click **Authorize** (top right)
3. In the **HTTPBearer** field paste: `<your-token>` (without the `Bearer ` prefix)
4. Click **Authorize** → **Close**

All subsequent Swagger requests will include the `Authorization: Bearer <token>` header.

### 3. Create org → project → experiment → API token

5. **Create an organisation** — `POST /organizations`
   ```json
   { "name": "My Org", "description": "" }
   ```
   → copy the returned `id`

6. **Create a project** — `POST /projects`
   ```json
   { "name": "My Project", "description": "", "organization_id": "<org-id>" }
   ```
   → copy the returned `id`

7. **Create an experiment** — `POST /experiments`
   ```json
   { "name": "My Experiment", "description": "", "project_id": "<project-id>", "country_name": "", "country_iso_code": "", "region": "", "on_cloud": false }
   ```
   → copy the returned `id` — this is your **`experiment_id`**

8. **Create a project API token** — `POST /projects/{project_id}/api-tokens`
   ```json
   { "name": "my-token", "access": 3 }
   ```
   → copy the returned `token` — this is your **`api_key`**

> **Important:** set `"access": 3` (`READ_WRITE`) when creating the token. The default value `2` (`WRITE`) triggers a known upstream bug where a cross-session DB update causes a ROLLBACK, making the token appear invalid and returning 403.

---

## Configure the codecarbon client

Install the client on any machine that will track emissions:

```bash
pip install codecarbon
```

### Local (laptop / VM pointing to local server)

Create or edit `~/.codecarbon.config`:

```ini
[codecarbon]
save_to_api = True
api_endpoint = http://localhost:8000
experiment_id = <experiment-uuid>
api_key = <project-api-token>
```

Or pass parameters directly in Python:

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(
    save_to_api=True,
    api_endpoint="http://localhost:8000",
    experiment_id="<experiment-uuid>",
    api_key="<project-api-token>",
)
tracker.start()
# ... your code ...
tracker.stop()
```

### Production (remote machine pointing to deployed server)

Replace `localhost:8000` with the production HTTPS URL:

```ini
[codecarbon]
save_to_api = True
api_endpoint = https://codecarbon-api.yourdomain.com
experiment_id = <experiment-uuid>
api_key = <project-api-token>
```

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(
    save_to_api=True,
    api_endpoint="https://codecarbon-api.yourdomain.com",
    experiment_id="<experiment-uuid>",
    api_key="<project-api-token>",
)
tracker.start()
# ... your code ...
tracker.stop()
```

> **VM / firewall note:** if using a VM as the API host, ensure port `8000` is open in the firewall for local deployments, or that ports `80`/`443` are open for production (Traefik handles TLS termination).

---

## Context variables reference

The `api_key` is sent as the `x-api-token` HTTP header by the codecarbon client.  
The `experiment_id` groups runs under a named experiment within a project.  
Emissions data flows: machine → `POST /emissions` → postgres → queryable via `/runs`, `/emissions` endpoints or the CodeCarbon UI.
