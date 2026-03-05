# Requirements Files

This directory contains pre-compiled requirements files for different use cases.

## requirements-api.txt

This file contains all dependencies needed to run the CodeCarbon API server (carbonserver).

### Updating the file

When you modify dependencies in `carbonserver/pyproject.toml`, you **must** regenerate this file:

```bash
uv pip compile carbonserver/pyproject.toml --output-file requirements/requirements-api.txt
```

Then commit the updated file.
