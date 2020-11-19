# Release process

- Merge all PRs
- Create and Merge a PR bumping the version in https://github.com/mlco2/codecarbon/blob/master/setup.py and https://github.com/mlco2/codecarbon/blob/master/meta.yaml.
- Wait for the Github Action `ReleaseDrafter` to finish running on the merge commit.
- Edit the Draft release on Github and give it a tag, `v1.0.0` for the version 1.0.0. Github will automatically create a Git tag for it.
- Go to the `package` Github action for the merge commit, wait for the run to finish, then download the two artifacts `pypi_dist` and `conda_dist`.
- In a python environment, install and update twine with `pip install -U twine`. Unzip the `pypi_dist.zip` archive in a temporary directory with `unzip pypi_dist.zip` and upload all files inside with `twine upload codecarbon*`.
- Unzip the `conda_dist.zip` in a temporary directory with `unzip conda_dist.zip`. Start a Docker image in the same directory and bind-mount the current directory with: `docker run -ti --rm=true -v (pwd):/data:z  continuumio/anaconda3:2020.02`. Inside the docker container, run `anaconda upload /data/noarch/codecarbon-*`.
