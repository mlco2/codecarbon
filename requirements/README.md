# Requirements Files

This directory contains pre-compiled requirements files for different use cases.

## requirements-api.txt

This file contains all dependencies needed to run the CodeCarbon API server (carbonserver).

### Updating the file

When you modify dependencies in `pyproject.toml` (especially those under the `[project.optional-dependencies.api]` section), you **must** regenerate this file:

```bash
uv pip compile pyproject.toml --extra api --output-file requirements/requirements-api.txt
```

Then commit the updated file.
