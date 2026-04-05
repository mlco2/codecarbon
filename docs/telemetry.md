# Telemetry

CodeCarbon can send **anonymous usage and diagnostics** over HTTPS to help maintainers improve the library. Optionally, you can opt in to **public** sharing of **run-level emissions summaries** (for example for leaderboards). This page explains the three tiers, **what** is collected in each case, **why**, and how to control it.

Telemetry HTTP uses its own **base URL resolution**: `CODECARBON_TELEMETRY_API_ENDPOINT`, optional JSON `telemetry_api_endpoint` in the `[codecarbon]` telemetry blob, then the same hierarchical `api_endpoint` / `CODECARBON_API_ENDPOINT` as the rest of CodeCarbon (default `https://api.codecarbon.io`). **Dashboard** uploads (`save_to_api`, `CodeCarbonAPIOutput`) still use only `api_endpoint` + `api_key`; you can point telemetry at a different host in the same process.

## Telemetry tiers

| Tier | How to choose it | What is sent | Why |
|------|-------------------|--------------|-----|
| **Off** | `CODECARBON_TELEMETRY=off`, CLI setup, or saved preference | **Nothing** over the network for telemetry | You do not want CodeCarbon to phone home with usage statistics or emissions summaries. |
| **Internal** | Default when no preference exists, or `CODECARBON_TELEMETRY=internal`, or CLI | After each `EmissionsTracker.stop()`, one **`POST /telemetry`** with **environment, hardware, usage, and library diagnostics** (no per-run CO₂ totals on this request) | Helps the team understand real-world setups (OS, GPUs, frameworks, tracking modes), spot breakage patterns, and prioritise improvements—without publishing your emissions. |
| **Public** | `CODECARBON_TELEMETRY=public`, or CLI | Same **`POST /telemetry`** as internal **plus**, when configured, a second **`POST /emissions`** with **energy, emissions, duration, and utilization averages** for that run (skipped if the run is shorter than one second) | Lets you contribute **aggregated run outcomes** for transparency and leaderboards, alongside the same diagnostic bundle as internal tier. |

The client adds a field **`telemetry_tier`** (`internal` or `public`) on `/telemetry` so the server knows the user’s choice.

## What we collect by tier

### Off

- **No telemetry HTTP requests.** Local tracking (CSV, logs, your own API key flows) behaves as you configure it separately.

### Internal — `POST /telemetry` only

**Goal:** Improve CodeCarbon for everyone without exposing your experiment’s carbon results.

Typical categories in the payload (exact keys may evolve with the library):

- **Environment:** Python version, OS, CodeCarbon version, how Python/CodeCarbon appear to be installed (heuristic).
- **Hardware:** CPU/GPU model and counts, RAM size, CUDA/cuDNN when detectable—not your hostname or raw serial numbers.
- **How you use CodeCarbon:** Tracking mode (`machine` / `process`), which output backends are enabled (file, logger, API, …), power measurement interval, which hardware types are tracked.
- **ML stack (import-based):** Whether common frameworks (e.g. PyTorch, TensorFlow, Transformers) are present and their versions, to prioritise integrations.
- **Context heuristics:** e.g. notebook vs script, CI hints, container hints, optional **cloud provider / region** strings when your tracker knows them (same metadata you already use for emission factors).
- **Diagnostics:** Whether RAPL or certain GPU paths worked, whether hardware detection succeeded, optional non-sensitive error snippets to debug widespread failures.

**Not sent on `/telemetry`:** Per-run **kg CO₂**, **kWh**, **duration**, or **utilization averages** (those belong on the separate emissions payload for public tier only).

### Public — `POST /telemetry` and optionally `POST /emissions`

- **Everything internal sends on `/telemetry`** (same reasons: product quality and compatibility).
- **Additionally**, when you have configured a **telemetry auth token** (`CODECARBON_TELEMETRY_API_KEY`, or `telemetry_api_key` / legacy `telemetry_project_token` in the telemetry JSON, etc.), a **second request** sends a **flat summary** of that run: total emissions, energy by component where available, duration, and CPU/GPU/RAM utilization averages.

**Why a second request:** Keeps **usage/diagnostics** and **publishable run metrics** separated so internal analytics can stay minimal while public/leaderboard flows can validate and store emissions-shaped records.

## Privacy and data minimisation

- **No deliberate collection of personal identifiers** (name, email, etc.) in the telemetry payloads described above.
- **Some fields are pseudonymous or coarse by design** (e.g. a short hash of the Python executable path, coarse cloud region strings rather than precise GPS in telemetry).
- **You control the tier** via environment variable, CLI, or saved preference.
- **Public emissions** use the **telemetry** token chain, not your dashboard `api_key` / `CODECARBON_API_KEY`; treat telemetry tokens like any other secret.
- For **retention, deletion, and legal requests**, follow the policies of the **API operator** hosting the telemetry base URL (and separately the dashboard API host if you use it).

## Configuration

### Environment variable (tier)

```bash
export CODECARBON_TELEMETRY=internal   # or public, or off
```

### Telemetry base URL and auth (separate from dashboard)

- **`CODECARBON_TELEMETRY_API_ENDPOINT`** (optional) — overrides where `/telemetry` and `/emissions` are sent; otherwise JSON `telemetry_api_endpoint`, then **`api_endpoint` / `CODECARBON_API_ENDPOINT`**.
- **`CODECARBON_TELEMETRY_API_KEY`** (or telemetry JSON keys) — required for **`POST /emissions`** in public tier when you want emissions uploaded. **Not** the same as **`api_key` / `CODECARBON_API_KEY`**, which are only for dashboard / `save_to_api` logging.

### CLI

```bash
codecarbon telemetry setup   # interactive
codecarbon telemetry config    # show effective tier and whether a token is available
```

### In Python (tier)

Tier is **not** a constructor argument on `EmissionsTracker`. Set the environment variable before import/run, use `codecarbon telemetry setup`, or use the public helpers:

```python
from codecarbon import set_telemetry

set_telemetry("internal", dont_ask_again=True)
```

## When data is sent

Telemetry runs **once per completed tracker session**, when **`EmissionsTracker.stop()`** (or equivalent base implementation) finishes flushing outputs—not continuously while your job runs.

## Disabling telemetry

```bash
export CODECARBON_TELEMETRY=off
```

Or use `codecarbon telemetry setup` and choose **off**, or call `set_telemetry("off", dont_ask_again=True)` early in your process.

## Further reading (developers)

For the exact HTTP contract, payload exclusions, and backend implementation checklist, see **`TELEMETRY_README.md`** at the root of the CodeCarbon source repository (next to the `docs/` folder). That file is aimed at contributors and API implementers; it is not part of the built docs site.
