# Requirements Files

This directory contains pre-compiled requirements files for different use cases.

## requirements-api.txt

This file contains all dependencies needed to run the CodeCarbon API server (carbonserver).

### Updating the file

When you modify dependencies in `carbonserver/pyproject.toml`, you **must** regenerate this file:

```bash
uv pip compile carbonserver/pyproject.toml --generate-hashes --no-emit-package codecarbon --output-file requirements/requirements-api.txt
```

Then commit the updated file.

`codecarbon` itself is excluded from this file on purpose. carbonserver depends on
it as a path dependency (see `[tool.uv.sources]` in `carbonserver/pyproject.toml`),
which compiles to an unhashed `-e ..` entry that `--require-hashes` rejects. Its
*transitive* dependencies are still resolved and hashed here; only the local
project is omitted, and the API Dockerfile installs it separately with
`--no-deps`.
