"""Script to check version in pyproject.toml and
compare it to versions in PyPi JSON API.

If the version exist, exit with 1 to break CI.

Sample call:
python3 deploy/check_version.py -p leximpact-socio-fisca-simu-etat
"""

import argparse

import requests


def get_local_version():
    """
    Read the version in pyproject.toml
    :return: The version
    """
    import re

    VERSIONFILE = "codecarbon/__init__.py"
    verstrline = open(VERSIONFILE, "rt").read()
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        return mo.group(1)
    else:
        raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))


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
    return v


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--package",
        type=str,
        default="",
        required=True,
        help="The name of the package",
    )
    parser.add_argument(
        "-o",
        "--onlyprintversion",
        action="store_true",
        default=False,
        help="Only print the local version of the package.",
    )
    args = parser.parse_args()
    versions = get_versions_from_pypi(args.package)
    local_version = get_local_version()
    if args.onlyprintversion:
        print(local_version)
    elif local_version.lower().strip() in versions:
        print(f"Version {local_version} already exist on PyPi !")
        print("Please run 'poetry version patch && make precommit' and commit changes.")
        exit(1)
