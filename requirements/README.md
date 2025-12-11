# Requirements Files

This directory contains pre-compiled requirements files for different use cases.

## requirements-api.txt

This file contains all dependencies needed to run the CodeCarbon API server (carbonserver).

### Updating the file

When you modify dependencies in `pyproject.toml` or when `uv.lock` changes (especially those under the `[project.optional-dependencies.api]` section), you **must** regenerate this file:

```bash
uv export --extra api --no-hashes --format requirements-txt > requirements/requirements-api.txt
```

Then commit the updated file.

**Note:** This uses `uv.lock` to ensure fully reproducible builds with the exact same versions that are tested in CI.

### CI Check

A GitHub Actions workflow (`.github/workflows/check-requirements.yml`) automatically verifies that this file is up-to-date on every pull request that modifies `pyproject.toml`. If the check fails, simply run the command above and commit the changes.