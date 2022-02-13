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


Create a virtual environment using `conda` for easier management of dependencies and packages.
For installing conda, follow the instructions on the [official conda website](https://docs.conda.io/projects/conda/en/latest/user-guide/install/)

```bash
conda create --name codecarbon python=3.8
conda activate codecarbon
```

Install from sources in development mode :

```bash
git clone https://github.com/mlco2/codecarbon
pip install -e .
```


### Tests


Make sure that the [`tox` package](https://tox.readthedocs.io/en/latest/example/package.html) is available to run tests and debug:

```
pip install tox
```

You can run tests by simply entering tox in the terminal when in the root package directory, and it will run the unit tests.

```
tox
```

This will not run test that may failed because of your environment (no CO2 Signal API token, no PowerGadget...), if you want to run all package tests :

```
tox -e all
```

You can also test your specific test in an isolated fashion to develop and debug them:

```
$ python -m unittest tests.test_your_feature

# or

$ python -m unittest tests.test_your_feature.YourTestCase.test_function
```

To test the API, see [how to deploy it](#local_deployement) first.


Core & external classes are unit tested, with one test file per class. Mosts pull-requests are expected to contains new tests or test update, if you are unusure what to test / how to test it, please put it in the pull-request description and the maintainers will help you.


### Versionning


To add a new feature to codecarbon, the following workflow is applied :
- Master branch is protected
- To contribute to an already [prioritized](https://github.com/orgs/mlco2/projects/1) feature, you can create a branch from master and open a draft PR
- Documenting the intent & the limits of a contribution in a dedicated issue or in the pull request helps the review
- Once automated tests pass, the PR is reviewed and merged by the repository maintainers


### <a name="local_deployement"></a> Local deployment


To test locally the dashboard application, you can run try it out on a sample data file such as the one in `examples/emissions.csv`, and run it with the following command from the code base:
```bash
python codecarbon/viz/carbonboard.py --filepath="examples/emissions.csv"
```

If you have the package installed, you can run the CLI command:

```bash
carbonboard --filepath="examples/emissions.csv" --port=xxxx
```

To test the current version of the dashboard, switch to the dashboard branch and run

```bash
python carbon_board_API.py
```

### Coding style && Linting

The coding style and linting rules are automatically applied and enforce by [pre-commit](https://pre-commit.com/). This tool helps to maintain the same code style across the code-base to ease the review and collaboration process. Once installed ([https://pre-commit.com/#installation](https://pre-commit.com/#installation)), you can install a Git hook to automatically run pre-commit (and all configured linters/auto-formatters) before doing a commit with `pre-commit install`. Then once you tried to commit, the linters/formatters will run automatically. It should display something similar to:

```
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

If any of the linters/formatters failed, check the difference with `git diff`, add the differences if there is no behavior changes (isort and black might have change some coding style or import order, this is expected it is their jobs) with `git add` and finally try to commit again `git commit ...`.

You can also run `pre-commit` with `pre-commit run -v` if you have some changes staged but you are not ready yet to commit.


### Packaging

Dependencies are defined in three different places:

- In [setup.py](setup.py#L7), those are the dependencies for the Pypi package.
- In [.conda/py36/meta.yaml](.conda/py36/meta.yaml#21), those are dependencies for the Conda package targeting Python 3.6.
- In [.conda/py37-plus/meta.yaml](.conda/py37-plus/meta.yaml#L21), those are the dependencies for the Conda pacakge targeting Python 3.7 and higher versions.

We are currently support Python 3.6 at minimum and new dependencies must be compatible with Python 3.6.

### Alternative ways of contributing


You have a cool idea, but do not know know if it fits with Code Carbon ? You can create an issue to share :
- the code, via the Github repo or [Binder](https://mybinder.org/), to share executable notebooks
- a webapp, using [Voilà](https://github.com/voila-dashboards/voila), [Dash](https://github.com/plotly/dash) or [Streamlit](https://github.com/streamlit/streamlit)
- ideas for improvement about the tool or its documentation


### Release process


- Merge all PRs
- Create and Merge a PR bumping the version in https://github.com/mlco2/codecarbon/blob/master/setup.py and https://github.com/mlco2/codecarbon/blob/master/meta.yaml.
- Wait for the Github Action `ReleaseDrafter` to finish running on the merge commit.
- Edit the Draft release on Github and give it a tag, `v1.0.0` for the version 1.0.0. Github will automatically create a Git tag for it.
- Go to the `package` Github action for the merge commit, wait for the run to finish, then download the two artifacts `pypi_dist` and `conda_dist`.
- In a python environment, install and update twine with `pip install -U twine`. Unzip the `pypi_dist.zip` archive in a temporary directory with `unzip pypi_dist.zip` and upload all files inside with `twine upload codecarbon*`.
- Unzip the `conda_dist.zip` in a temporary directory with `unzip conda_dist.zip`. Start a Docker image in the same directory and bind-mount the current directory with: `docker run -ti --rm=true -v (pwd):/data:z  continuumio/anaconda3:2020.02`. Inside the docker container, run `anaconda upload --user codecarbon /data/noarch/codecarbon-*.tar.bz2`.

### API

To run the API locally, the easiest way is Docker. Launch this command in the project directory:
```
docker-compose up -d
```
Please see [Docker specific documentation](./docker/README.md) for more informations.
When up, the API documentation is locally available at the following URL : http://localhost:8008/redoc and can be used for testing.


In order to connect make codecarbon automatically connect to the local API, create a file `.codecarbon.config` with the content:
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
#### Deployment

The API is availiable to everyone from https://api.codecarbon.io but if you want to deploy it for yourself, here is the instructions.

To deploy the API we use [Clever Cloud](https://www.clever-cloud.com/) , an IT Automation platform. They manage all the hard ops work while we focus on the Code Carbon value.

Here is the Clever Cloud configuration if you want to reproduce it :
```
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
```
git remote add deploy git+ssh://git@push-n2-par-clevercloud-customers.services.clever-cloud.com/app_<secret_do_not_share>.git
git push deploy master:master
```
Yeah, no so hard, isn't it ?

See (the doc)[https://www.clever-cloud.com/doc/getting-started/quickstart/] for more informations.

Please note that Clever Cloud host Code Carbon for free because they like our project.

### License


By contributing your code, you agree to license your contribution under the terms of the [MIT License](LICENSE).

All files are released with the MIT license.
