# Contribution process

(New to open-source? [Here's a guide to help you](https://opensource.guide/how-to-contribute/))

1. Fork `codecarbon`
2. Create a branch to work from
3. Create a Pull-Request on this repo **in draft mode**
4. Contribute code (commit and push frquently, with intelligible commit messages)
5. Write tests in `tests/` (duh ?).
6. Explain the PR in its *Conversation* section

### Tests

If you want to contribute, make sure that the [`tox` package](https://tox.readthedocs.io/en/latest/example/package.html) is available to run tests and debug:

```
pip install tox
```

You can run tests by simply entering tox in the terminal when in the root package directory, and it will run the predefined tests.

```
tox
```
In order to contribute a change to our code base, please submit a pull request (PR) via GitHub and someone from our team will go over it and accept it.

You can also test your specific test in an isolated fashion to develop and debug them:

```
$ python -m unittest tests.test_your_feature

# or

$ python -m unittest tests.test_your_feature.YourTestCase.test_function
```

# Release process

- Merge all PRs
- Create and Merge a PR bumping the version in https://github.com/mlco2/codecarbon/blob/master/setup.py and https://github.com/mlco2/codecarbon/blob/master/meta.yaml.
- Wait for the Github Action `ReleaseDrafter` to finish running on the merge commit.
- Edit the Draft release on Github and give it a tag, `v1.0.0` for the version 1.0.0. Github will automatically create a Git tag for it.
- Go to the `package` Github action for the merge commit, wait for the run to finish, then download the two artifacts `pypi_dist` and `conda_dist`.
- In a python environment, install and update twine with `pip install -U twine`. Unzip the `pypi_dist.zip` archive in a temporary directory with `unzip pypi_dist.zip` and upload all files inside with `twine upload codecarbon*`.
- Unzip the `conda_dist.zip` in a temporary directory with `unzip conda_dist.zip`. Start a Docker image in the same directory and bind-mount the current directory with: `docker run -ti --rm=true -v (pwd):/data:z  continuumio/anaconda3:2020.02`. Inside the docker container, run `anaconda upload --user codecarbon /data/noarch/codecarbon-*.tar.bz2`.
