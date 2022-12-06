"""Script to check version and
compare it to versions in PyPi JSON API.

If the version exist, exit with 1 to break CI.

Sample call:
python3 github/check_version.py
"""

import argparse
import re
import sys

import requests


def get_local_version(filepath="codecarbon/__init__.py"):
    """
    Read the version in the file given in parameter
    :return: The version
    """

    filecontent = open(filepath, "rt").read()
    mo = re.search(r"version(?:_*)\s?=\s?['\"]([^'\"]*)['\"]", filecontent, re.M)
    if mo:
        return mo.group(1)
    raise RuntimeError(f"Unable to find version string in {filepath}")


def get_versions_from_pypi(package_name: str = "") -> dict:
    """Get package versions from PyPi JSON API.

    ::package_name:: Name of package to get infos from.
    ::return:: A list of versions.
    """
    if package_name == "":
        raise ValueError("Package name not provided.")
    url = f"https://pypi.org/pypi/{package_name}/json"
    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception(f"ERROR calling PyPI ({url}) : {resp}")
    resp = resp.json()
    versions = []
    for v in resp["releases"]:
        versions.append(v.lower().strip())
    return versions


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--onlyprintversion",
        action="store_true",
        default=False,
        help="Only print the local version of the package.",
    )
    args = parser.parse_args()
    versions = get_versions_from_pypi("codecarbon")
    module_version = get_local_version()
    meta_version = get_local_version(".conda/meta.yaml")
    setup_version = get_local_version("setup.py")
    local_versions = [module_version, meta_version, setup_version]
    if local_versions.count(local_versions[0]) != len(local_versions):
        print("All local versions did not match !")
        print(f"__init__.py : {module_version}")
        print(f"setup.py : {setup_version}")
        print(f"meta.yaml : {meta_version}")
        sys.exit(1)
    if args.onlyprintversion:
        print(setup_version)
    elif module_version.lower().strip() in versions:
        print(f"Version {setup_version} already exist on PyPi !")
        print("Please bump the version in setup.py, __init__.py and meta.yaml !.")
        sys.exit(1)
    else:
        print(
            f"All good !\nLocal version is {setup_version}\nPyPi versions are {versions}"
        )
