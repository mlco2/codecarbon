# Maintainer guide

Maintainer-only runbook: releasing CodeCarbon, deploying the API and the dashboard, and
operating the production database. Contributors want the
[contributing guide](how-to/contributing.md) and the
[development guide](how-to/development.md) instead.

## Release process

- Merge all PRs.
- Open a terminal and make sure you are not in a venv with `deactivate`.
- Create a PR bumping the version with `uv run bumpver update --patch`. For a release candidate, use `uv run bumpver update --set-version 3.0.0_rc1`.
- Run `uv run python .github/pyproject_versions.py -c` to check version consistancy.
- No manual step is needed for the citation: `bumpver` also updates the `version:` line in `CITATION.cff`. Only `date-released:` may need a manual touch.
- Update the dependencies with `uv sync --upgrade`
- [Build the documentation](how-to/development.md#build-documentation) with `uv run --only-group doc task docs`.
- Push the changes.
- Merge the PR.
- Wait for the Github Action `ReleaseDrafter` to finish running on the merge commit.
- [Edit the Draft release](https://github.com/mlco2/codecarbon/releases/) on Github and give it a tag, `v1.0.0` for the version 1.0.0. Github will automatically create a Git tag for it. Complete help [here](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).
-   A [Github Action](https://github.com/mlco2/codecarbon/actions) _Upload Python Package_ will be run automaticaly to upload the package.

### Test the release

After the release on PyPi, please test it in a fresh environment:

```sh
cd /tmp
rm -rf cc_rel_test
python -m venv cc_rel_test
source cc_rel_test/bin/activate
pip install codecarbon
# Check you have the last version
codecarbon --version
codecarbon monitor --offline --country-iso-code FRA
# Stop it with Ctrl+C if it works
# Then clean up
rm -rf cc_rel_test
```

And check if the doc looks good on [docs.codecarbon.io](https://docs.codecarbon.io/).

### Test the build in Docker

If you want to check the build is working, you could run:

```bash
rm dist/*
uv build
docker run -it --rm -v $PWD:/data python:3.13 /bin/bash
pip install pytest pytest-mock requests-mock responses pandas
pip install --no-cache-dir /data/dist/codecarbon-*.whl -U --force-reinstall
cp /data/tests/test_package_integrity.py .
pytest test_package_integrity.py
```

## Conda-forge packaging

CodeCarbon is distributed on [conda-forge](https://anaconda.org/conda-forge/codecarbon)
in addition to PyPI, so that conda users can install it with:

```bash
conda install -c conda-forge codecarbon
```

Nothing in this repository builds that package. Conda-forge builds every package from
a dedicated repository called a *feedstock*, ours being
[conda-forge/codecarbon-feedstock](https://github.com/conda-forge/codecarbon-feedstock).
The build instructions live there in `recipe/meta.yaml`, and the people allowed to
approve changes are listed at the bottom of that file under `extra: recipe-maintainers`.

### How a release reaches conda-forge

1. We publish to PyPI, as described in [Release process](#release-process).
2. A few hours later `regro-cf-autotick-bot` notices the new version, and opens a PR on
   the feedstock bumping the version and the source `sha256`. It also re-reads the
   dependencies from the published package and updates the recipe accordingly.
3. Conda-forge CI builds the package and runs the tests declared in the recipe, which
   for us are `pip check` plus `codecarbon --help`.
4. `conda-forge.yml` sets `bot: automerge: true`, so the PR merges itself once CI is
   green and the package is uploaded to the `conda-forge` channel.

A normal release therefore needs **no action** from us. `pip check` is the safety net:
if a dependency is missing or is named differently on conda-forge, CI fails, the PR
stays open, and a maintainer has to step in.

### Updating the recipe by hand

Needed when the bot PR fails, or when the recipe has drifted from `pyproject.toml`
(a new dependency, a dropped Python version, a renamed entry point).

Two conda-forge rules make this different from a normal PR:

- **Always work from a personal fork.** Conda-forge refuses PRs opened from a branch of
  the feedstock itself, and its bot cannot push to a fork owned by an organisation. Fork
  to your own account, not to `mlco2`.
- **Never edit the generated files by hand.** `README.md`, `.ci_support/`, and the CI
  workflows are produced by `conda-smithy`. To refresh them, comment on the PR:

  ```text
  @conda-forge-admin, please rerender
  ```

  The bot pushes the regenerated files to your branch. A feedstock that has not been
  rerendered for a long time will fail to build at all, because its pinned CI container
  eventually becomes too old for conda-forge tooling.

To update the recipe itself:

- Set `version`, and take the matching `sha256` from the sdist on
  [PyPI](https://pypi.org/project/codecarbon/#files).
- Mirror the `dependencies` of our `pyproject.toml` into `requirements: run`. Conda
  package names occasionally differ from PyPI ones, and environment markers such as
  `python_version >= "3.14"` cannot be expressed in a `noarch: python` recipe.
- Do not hardcode a Python version: use `{{ python_min }}`, which comes from
  conda-forge's global pinning.
- The optional `carbonboard` extra is shipped as a separate `codecarbon-viz`
  metapackage, so its dependencies must be updated there too.

Adding someone to `extra: recipe-maintainers` requires that person to comment on the PR
to confirm.

## Restore database from a production Backup

```sh
docker cp postgresql_*.dump postgres_codecarbon:/tmp
docker exec -it postgres_codecarbon bash
export BACKUP_USER=upwnpbdktjvnoks0foxq
export BACKUP_DB=bnrwiktgr4hzukt1xseg
psql -U $POSTGRES_USER -d $POSTGRES_DB -c "CREATE USER $BACKUP_USER WITH PASSWORD '$POSTGRES_PASSWORD';"
psql -U $POSTGRES_USER -d $POSTGRES_DB -c "ALTER USER $BACKUP_USER CREATEDB;"
createdb -U $BACKUP_USER $BACKUP_DB
psql -U $BACKUP_USER -d $POSTGRES_DB -c "CREATE DATABASE $BACKUP_DB;"
pg_restore -d $BACKUP_DB -U $BACKUP_USER --jobs=8 --clean --create /tmp/postgresql_*.dump
psql -U $BACKUP_USER -d $BACKUP_DB -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO \"$POSTGRES_USER\";"
psql -U $POSTGRES_USER -d $BACKUP_DB -c "ALTER DATABASE $POSTGRES_DB RENAME TO \"$POSTGRES_DB-backup\";"
psql -U $BACKUP_USER -d $POSTGRES_DB-backup -c "ALTER DATABASE $BACKUP_DB RENAME TO $POSTGRES_DB;"
```

### Clean the database

To remove orphans (elements without run) from the database, run:

```sql
CALL public.spcc_purgeduplicatedata();
```

## Deployment

### API

The API is available to everyone from https://api.codecarbon.io, but if you want to deploy it for yourself, here are the instructions.

To deploy the API we use [Clever Cloud](https://www.clever-cloud.com/), an IT Automation platform. They manage all the hard ops work while we focus on the Code Carbon value.

Here is the Clever Cloud configuration if you want to reproduce it:

```conf
APP_FOLDER="carbonserver"
CC_PIP_REQUIREMENTS_FILE="requirements.txt"
CC_POST_BUILD_HOOK="cd $APP_HOME/carbonserver && python3 -m alembic -c carbonserver/database/alembic.ini upgrade head"
CC_PYTHON_BACKEND="uvicorn"
CC_PYTHON_MODULE="main:app"
CC_PYTHON_VERSION="3.13"
DATABASE_URL="postgresql://secret_do_not_publish_this"
PORT="8080"
```

The `CC_` prefix is Clever Cloud's, not CodeCarbon's.

To deploy,

```sh
git remote add deploy git+ssh://git@push-n2-par-clevercloud-customers.services.clever-cloud.com/app_<secret_do_not_share>.git
git push deploy master:master
```

See [the doc](https://www.clever-cloud.com/doc/getting-started/quickstart/) for more informations.

Please note that Clever Cloud host Code Carbon for free because they like our project.

### Dashboard

Same as for the API, for example to deploy the branch `fix-unit` to CleverCloud:

```sh
git push clever-dashboard fix-unit:master
```

Config on CleverCloud:

```sh
APP_FOLDER="dashboard"
CC_PIP_REQUIREMENTS_FILE="requirements-dashboard.txt"
CC_PYTHON_MODULE="carbon_board_API:server"
CC_PYTHON_VERSION="3.13"
CODECARBON_API_URL="https://api.codecarbon.io"
PORT="8000"
```
