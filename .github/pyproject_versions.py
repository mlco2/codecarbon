# Read package version in pyproject.toml and replace it in .conda/recipe.yaml

import argparse
import logging
import tomllib

logging.basicConfig(level=logging.INFO, format="%(message)s")
PACKAGE_VERSION = "X.X.X"


def get_versions():
    """
    Read package version and deps in pyproject.toml
    """
    with open("./pyproject.toml", "rb") as file:
        # Use tomlib to parse pyproject.toml
        content = tomllib.load(file)

    # Extract the version of the package
    package_version = (
        content.get("tool", {}).get("bumpver", {}).get("current_version", None)
    )
    if package_version is None:
        raise Exception("Package version not found in pyproject.toml")
    # Extract dependencies
    dependencies = content.get("project", {}).get("dependencies", None)
    if dependencies is None:
        raise Exception("Dependencies not found in pyproject.toml")
    return {
        "package_version": package_version,
        "dependencies": dependencies,
    }


def replace_in_file(filepath: str, info: dict):
    """
    ::filepath:: Path to recipe.yaml, with filename
    ::info:: Dict with information to populate
    """
    with open(filepath, "rt") as fin:
        meta = fin.read()
    # Replace with info from pyproject.toml
    if PACKAGE_VERSION not in meta:
        raise Exception(f"{PACKAGE_VERSION=} not found in {filepath}")
    meta = meta.replace(PACKAGE_VERSION, info["package_version"])
    if "    - dependencies" not in meta:
        raise Exception(f'"    - dependencies" not found in {filepath}')
    dependencies = ""
    for dep in info["dependencies"]:
        dependencies += f"    - {dep}\n"
    meta = meta.replace("    - dependencies", dependencies)
    with open(filepath, "wt") as fout:
        fout.write(meta)
    logging.info(
        f"File {filepath} has been updated with informations from pyproject.toml."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r",
        "--replace",
        type=bool,
        default=False,
        required=False,
        help="replace in file",
    )
    parser.add_argument(
        "-f",
        "--filename",
        type=str,
        default=".conda/recipe.yaml",
        help="Path to recipe.yaml, with filename",
    )
    parser.add_argument(
        "-o",
        "--only_package_version",
        type=bool,
        default=False,
        help="Only display current package version",
    )
    args = parser.parse_args()
    info = get_versions()
    file = args.filename
    if args.only_package_version:
        print(f'{info["openfisca_france"]}')  # noqa: T201
        exit()
    logging.info("Versions :")
    print(info)  # noqa: T201
    if args.replace:
        logging.info(f"Replace in {file}")
        replace_in_file(file, info)
    else:
        logging.info("Dry mode, no replace made")
