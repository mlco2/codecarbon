
# Contributing to Code Carbon

(New to open-source? [Here's a guide to help you](https://opensource.guide/how-to-contribute/))

- [I have a question...](#questions)
- [I found a bug...](#bugs)
- [I have a feature request...](#features)
- [I have a contribution to share...](#process)

## <a name="questions"></a> Have a Question?

Please see the [FAQ](https://mlco2.github.io/codecarbon/faq.html) for questions.


## <a name="bugs"></a> Found a Bug?


If you've identified a bug in `codecarbon`, please [submit an issue](#issue) to the GitHub repo: [mlco2/codecarbon](https://github.com/mlco2/codecarbon/issues/new).  Please also feel free to submit a PR with a fix for the bug!


## <a name="features"></a> Have a Feature Request?


Feel free to describe your request by [submitting an issue](#issue) documenting the feature (with its intent) and a PR with a proposed implementation of the feature.




## <a name="process"></a> Ready to Contribute!

### <a name="issue"></a> Create an issue

Before submitting a new issue, please search the issues to make sure there isn't a similar issue already.
New issues can be created with in the [GitHub repo](https://github.com/mlco2/codecarbon/issues/new).


### Installation

CodeCarbon is a Python package, to contribute to it, you need to have Python installed on your machine, natively or with [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/).

Since April 2024 we use Hatch for managing development environment. Hatch manage the environments, even the Python versions, the dependencies and handle matrix testing. It is a good way to avoid conflicts with your system Python.

We have dropped support of Python 3.6 since version 2.0.0 of CodeCarbon.

It is not mandatory for small contribution, while not recommanded, you could just install the package with `pip install -e .`.

Please install [Hatch](https://hatch.pypa.io/) following [installation instruction](https://hatch.pypa.io/latest/install/), or with `pipx install hatch`.

Then, clone the repository and create the environment with:

```sh
git clone https://github.com/mlco2/codecarbon.git
cd codecarbon
hatch env create
```


### Tests

You can run the unit tests by running Hatch in the terminal when in the root package directory:

```sh
hatch run test:package
```

This will not run test that may fail because of your environment (no CO2 Signal API token, no PowerGadget...). If you want to run all package tests:

```sh
hatch run test:package-integ
```

You can also run your specific test in isolation to develop and debug them:

```sh
$ hatch run python -m unittest tests.test_your_feature

# or

$ hatch run python -m unittest tests.test_your_feature.YourTestCase.test_function
```

For example : `hatch run python -m unittest tests.test_energy.TestEnergy.test_wraparound_delta_correct_value`

To test the API, see [how to deploy it](#local_deployement) first.


Core and external classes are unit tested, with one test file per class. Most pull requests are expected to contain either new tests or test updates. If you are unusure what to test / how to test it, please put it in the pull request description and the maintainers will help you.

### Stress your computer

To test CodeCarbon, it is useful to stress your computer to make it use its full power:
- 7Zip is often already installed, running it with `7z b` makes a quick CPU test.
- [GPU-burn](https://github.com/wilicc/gpu-burn) will load test the GPU for a configurable duration.

`nvidia-smi` is a useful tool to see the metrics of the GPU and compare it with CodeCarbon.

### Versioning


To add a new feature to codecarbon, apply the following workflow:
- Master branch is protected
- To contribute to an already [prioritized](https://github.com/orgs/mlco2/projects/1) feature, you can create a branch from master and open a draft PR
- Documenting the intent & the limits of a contribution in a dedicated issue or in the pull request helps the review
- Once automated tests pass, the PR is reviewed and merged by the repository maintainers

### Debug in VS Code

Here is the launch.json to be able to debug examples and tests:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true,
            "env": { "PYTHONPATH": "${workspaceRoot}" }
        },
        {
            "name": "PyTest: Current File",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": [
                "${file}"
            ],
            "console": "integratedTerminal",
            "justMyCode": true,
            "env": { "PYTHONPATH": "${workspaceRoot}" }
        }
    ]
}
```

Then run opened test with this button:

![vscode_debug](docs/edit/images/vscode_debug.png)

### <a name="local_deployement"></a> Local deployment

## CSV Dashboard

To run locally the dashboard application, you can use it out on a sample data file such as the one in `examples/emissions.csv`, and run it with the following command from the code base:

```bash
hatch run carbonboard:run --filepath="examples/emissions.csv"

# or
pip install codecarbon["viz"]
python codecarbon/viz/carbonboard.py --filepath="examples/emissions.csv"
```

If you have the package installed, you can run the CLI command:

```bash
carbonboard --filepath="examples/emissions.csv" --port=8050
```

## API Dashboard

To test the new dashboard that uses the API, run:

```sh
hatch run dashboard:run
```

Then, click on the url displayed in the terminal.

By default, the dashboard is connected to the production API, to connect it to your local API, you can set the environment variable `CODECARBON_API_URL` to `http://localhost:8008` :

```sh
export CODECARBON_API_URL=http://localhost:8008
hatch run dashboard:run
```



### API

The easiest way to run the API locally is with Docker, it will set-up the Postgres database for you. Launch this command in the project directory:

```sh
hatch run api:docker

# or

docker-compose up -d
```

Please see [Docker specific documentation](./docker/README.md) for more informations.
When up, the API documentation is available locally at the following URL: http://localhost:8008/redoc and can be used for testing.

If you want to run the API without Docker, you can run the following commands:

```sh
hatch run api:local
```

In order to make codecarbon automatically connect to the local API, create a file `.codecarbon.config` with contents:
```
[codecarbon]
api_endpoint = http://localhost:8008
```

Before using it, you need an experiment_id, to get one, run:
```
codecarbon init
```

It will ask the API for an experiment_id on the default project and save it to `.codecarbon.config` for you.

Then you could run an example:
```
python examples/api_call_debug.py
```

📝 Edit the line `occurence = 60 * 24 * 365 * 100` to specify the number of minutes you want to run it.

### Test the API

To test the API, you can use the following command:

```sh
hatch run api:test-unit
```

```sh
export CODECARBON_API_URL=http://localhost:8008
hatch run api:test-integ

```

### Coding style && Linting

The coding style and linting rules are automatically applied and enforced by [pre-commit](https://pre-commit.com/). This tool helps to maintain the same code style across the code-base such to ease the review and collaboration process. Once installed ([https://pre-commit.com/#installation](https://pre-commit.com/#installation)), you can install a Git hook to automatically run pre-commit (and all configured linters/auto-formatters) before doing a commit with `hatch run dev:precommit-install`. Then once you tried to commit, the linters/formatters will run automatically. It should display something similar to:

```log
[INFO] Initializing environment for https://github.com/psf/black.
[INFO] Initializing environment for https://gitlab.com/pycqa/flake8.
[INFO] Installing environment for https://github.com/psf/black.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
[INFO] Installing environment for https://gitlab.com/pycqa/flake8.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
seed isort known_third_party.............................................Passed
isort....................................................................Failed
- hook id: isort
- files were modified by this hook

Fixing codecarbon/__init__.py

black....................................................................Passed
flake8...................................................................Passed
```

If any of the linters/formatters fail, check the difference with `git diff`, add the differences if there is no behavior changes (isort and black might have change some coding style or import order, this is expected it is their job) with `git add` and finally try to commit again `git commit ...`.

You can also run `pre-commit` with `pre-commit run -v` if you have some changes staged but you are not ready yet to commit.

It's nice to keep it up-to-date with `hatch run dev:precommit-update` sometimes.

### Packaging

Dependencies are defined in different places:

- In [pyproject.toml](pyproject.toml#L28), those are the dependencies for the Pypi package.
- In [requirements.txt](requirements.txt) and [requirements/](requirements/), those are locked dependencies managed by [Hatch plugin pip-compile](https://github.com/juftin/hatch-pip-compile), do not edit them.
- In [.conda/meta.yaml](.conda/meta.yaml#L21), those are the dependencies for the Conda pacakge targeting Python 3.7 and higher versions.

### Alternative ways of contributing


You have a cool idea, but do not know know if it fits with Code Carbon? You can create an issue to share:
- the code, via the Github repo or [Binder](https://mybinder.org/), to share executable notebooks
- a webapp, using [Voilà](https://github.com/voila-dashboards/voila), [Dash](https://github.com/plotly/dash) or [Streamlit](https://github.com/streamlit/streamlit)
- ideas for improvement about the tool or its documentation

### <a name="documentation"></a>Build Documentation 🖨️
No software is complete without great documentation!
To make generating documentation easier, we use [`sphinx` package](https://www.sphinx-doc.org/en/master/usage/installation.html#installation-from-pypi).

In order to make changes, edit the `.rst` files that are in the `/docs/edit` folder, and then run:

```
hatch run docs:build
```

to regenerate the html files.

### Release process

- Merge all PRs.
- Create a PR bumping the version in https://github.com/mlco2/codecarbon/blob/master/setup.py, https://github.com/mlco2/codecarbon/blob/master/codecarbon/_version.py and https://github.com/mlco2/codecarbon/blob/master/.conda/meta.yaml.
- Run `python3 .github/check_version.py` to check version consistancy.
- [Build Documentation](#documentation) if needed.
- Merge the PR.
- Wait for the Github Action `ReleaseDrafter` to finish running on the merge commit.
- [Edit the Draft release](https://github.com/mlco2/codecarbon/releases/) on Github and give it a tag, `v1.0.0` for the version 1.0.0. Github will automatically create a Git tag for it. Complete help [here](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).
- A [Github Action](https://github.com/mlco2/codecarbon/actions) _Upload Python Package_ will be run automaticaly to upload the package.
- For conda, we now have a [feedstock](https://github.com/conda-forge/codecarbon-feedstock/pulls) to publish to Conda-Forge channel.


If you still want to publish to the Anaconda CodeCarbon channel:

Start a Docker image in the same directory and bind-mount the current directory with:

`docker run -ti --rm=true -v $PWD:/data continuumio/anaconda3`.

Inside the docker container, run:
- `conda install conda-build conda-verify`
- `cd /data && mkdir -p conda_dist`
- `conda build --python 3.8 .conda/ -c conda-forge --output-folder conda_dist`
- `anaconda upload --user codecarbon /data/noarch/codecarbon-*.tar.bz2`


#### Restore database from a production Backup

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

#### Clean the database

To remove orphans (elements without run) from the database, run:

```sql
CALL public.spcc_purgeduplicatedata();
```

#### Deployment

##### API

The API is availiable to everyone from https://api.codecarbon.io, but if you want to deploy it for yourself, here are the instructions.

To deploy the API we use [Clever Cloud](https://www.clever-cloud.com/), an IT Automation platform. They manage all the hard ops work while we focus on the Code Carbon value.

Here is the Clever Cloud configuration if you want to reproduce it:
```conf
APP_FOLDER="carbonserver"
CC_PIP_REQUIREMENTS_FILE="requirements.txt"
CC_POST_BUILD_HOOK="cd $APP_HOME/carbonserver && python3 -m alembic -c carbonserver/database/alembic.ini upgrade head"
CC_PYTHON_BACKEND="uvicorn"
CC_PYTHON_MODULE="main:app"
CC_PYTHON_VERSION="3.8"
DATABASE_URL="postgresql://secret_do_not_publish_this"
PORT="8080"
```
_CC stand here for Clever Cloud, not Code Carbon_ 😉

To deploy,
```sh
git remote add deploy git+ssh://git@push-n2-par-clevercloud-customers.services.clever-cloud.com/app_<secret_do_not_share>.git
git push deploy master:master
```
Yeah, not so hard, is it?

See (the doc)[https://www.clever-cloud.com/doc/getting-started/quickstart/] for more informations.

Please note that Clever Cloud host Code Carbon for free because they like our project.

##### Dashboard

Same as for the API, for example to deploy the branh `fix-unit` to CleverCloud:
```sh
git push clever-dashboard fix-unit:master
```

Config on CleverCloud:
```sh
APP_FOLDER="dashboard"
CC_PIP_REQUIREMENTS_FILE="requirements-new.txt"
CC_PYTHON_MODULE="carbon_board_API:server"
CC_PYTHON_VERSION="3.8"
CODECARBON_API_URL="https://api.codecarbon.io"
PORT="8000"
```

### License

By contributing your code, you agree to license your contribution under the terms of the [MIT License](LICENSE).

All files are released with the MIT license.
