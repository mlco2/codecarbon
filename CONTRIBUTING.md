# Contributing to Code Carbon


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

To test the API, see [how to deploy it](#local_deployement) first.


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


To test the API (under development), switch to the api branch :
```bash
git checkout api
cd api
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

The API documentation is locally available at the following URL : http://localhost:8000/redoc and can be used for testing.


### Coding style


Using shared code conventions might help maintainers review & integrate PRs.
Rules that are actually observed : 
- core & external classes are unit tested, with one test file per class.
- naming & syntax follow the [PEP 8](https://pep8.org/) stle, tested with flake8 & black linters.
- added dependencies must be referenced to the corresponding requirements.txt files.


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


### License


By contributing your code, you agree to license your contribution under the terms of the [MIT License](LICENSE).

All files are released with the MIT license.
