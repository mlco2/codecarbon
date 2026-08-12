# Changelog

User-visible changes in CodeCarbon: new features, behaviour changes, deprecations,
removals, and anything that requires action on your side. For the full list of merged
pull requests, see the
[GitHub releases](https://github.com/mlco2/codecarbon/releases).

Deprecated features and their replacements are listed on the
[deprecations page](deprecations.md).

## Unreleased

### Added

- CPU power estimation now recognises the Apple M2, M3 and M4 chip families, so
  measurements on recent Apple Silicon no longer fall back to the default TDP
  ([#1256](https://github.com/mlco2/codecarbon/pull/1256)).

### Changed

- Updated the RAPL access instructions and the Ansible deployment role.

## 3.3.0 — 2026-08-04

### Added

- Windows support through the Energy Meter Interface (EMI), including multi-die
  machines. Windows measurements are no longer estimation-only where EMI is available
  ([#1263](https://github.com/mlco2/codecarbon/pull/1263)).

### Changed

- The API client now raises on HTTP errors instead of silently returning `None`.
  If you call `ApiClient` directly, expect exceptions where you previously got `None`
  and had to check for it ([#1277](https://github.com/mlco2/codecarbon/pull/1277)).

### Fixed

- Documented that `tracking_mode` affects RAM and CPU measurement, not only the
  process scope ([#1163](https://github.com/mlco2/codecarbon/pull/1163)).

## 3.2.9 — 2026-07-19

### Changed

- Substantially faster startup and lower measurement overhead: the tracker defers
  initialisation, caches hardware detection between runs, skips redundant GPU detail
  queries while monitoring, and reads only the header row when validating an existing
  CSV
  ([#1251](https://github.com/mlco2/codecarbon/pull/1251),
  [#1252](https://github.com/mlco2/codecarbon/pull/1252),
  [#1254](https://github.com/mlco2/codecarbon/pull/1254),
  [#1264](https://github.com/mlco2/codecarbon/pull/1264),
  [#1235](https://github.com/mlco2/codecarbon/pull/1235)).
- When using the hosted API, the run is only created on the first emission upload
  rather than at tracker start, so aborted runs no longer show up as empty runs
  ([#1253](https://github.com/mlco2/codecarbon/pull/1253)).

### Fixed

- Dashboard: run sums now exclude filtered-out runs, the date picker month arrows are
  aligned, and hovering the emissions chart no longer errors
  ([#1229](https://github.com/mlco2/codecarbon/pull/1229),
  [#1233](https://github.com/mlco2/codecarbon/pull/1233),
  [#1230](https://github.com/mlco2/codecarbon/pull/1230)).

## 3.2.8 — 2026-06-07

### Added

- Optional, opt-in telemetry ([#1171](https://github.com/mlco2/codecarbon/pull/1171)).
- BoAmps output format, with documentation and an example
  ([#1154](https://github.com/mlco2/codecarbon/pull/1154)).
- Documentation of what the hardware measurement actually covers
  ([#1204](https://github.com/mlco2/codecarbon/pull/1204)).

### Changed

- The web dashboard front end is now a plain React application
  ([#1076](https://github.com/mlco2/codecarbon/pull/1076)).

### Deprecated

- The `save_to_file`, `save_to_api`, `save_to_logger`, `save_to_prometheus` and
  `save_to_logfire` parameters. Use `output_methods=[OutputMethod.CSV, ...]` instead.
  They now emit a `DeprecationWarning`.

### Fixed

- `codecarbon monitor` in offline mode now uses `OfflineEmissionsTracker`
  ([#1202](https://github.com/mlco2/codecarbon/pull/1202)).
- macOS: CPU detection through `psutil` ([#1211](https://github.com/mlco2/codecarbon/pull/1211))
  and importing `amdsmi` when `libamd_smi` is absent
  ([#1201](https://github.com/mlco2/codecarbon/pull/1201)).
- Carbon intensity lookup for Nordic regions with the online tracker
  ([#1224](https://github.com/mlco2/codecarbon/pull/1224)).
- The CLI now warns when authentication validation falls back to the API
  ([#1209](https://github.com/mlco2/codecarbon/pull/1209)).

---

Changes released before 3.2.8 are listed on the
[GitHub releases page](https://github.com/mlco2/codecarbon/releases).
