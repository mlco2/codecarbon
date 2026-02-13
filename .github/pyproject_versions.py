# Read package version in pyproject.toml
# Also provides version coherence checking across multiple files

import argparse
import logging
import re
import sys
import tomllib

logging.basicConfig(level=logging.INFO, format="%(message)s")
PACKAGE_VERSION = "X.X.X"


def get_version_from_file(filepath: str, pattern: str) -> str:
    """
    Extract version from a file using a regex pattern.

    :param filepath: Path to the file to read
    :param pattern: Regex pattern to match the version
    :return: The version string found
    :raises: Exception if version not found
    """
    try:
        with open(filepath, "rt") as file:
            content = file.read()

        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return match.group(1)
        else:
            raise Exception(f"Version pattern '{pattern}' not found in {filepath}")
    except FileNotFoundError:
        raise Exception(f"File not found: {filepath}")


def get_all_versions() -> dict:
    """
    Read versions from all three files managed by bumpver.

    :return: Dict containing versions from all files
    """
    versions = {}

    # Get version from pyproject.toml
    try:
        with open("./pyproject.toml", "rb") as file:
            content = tomllib.load(file)
        versions["pyproject_toml"] = (
            content.get("tool", {}).get("bumpver", {}).get("current_version", None)
        )
        if versions["pyproject_toml"] is None:
            raise Exception(
                "current_version not found in pyproject.toml [tool.bumpver] section"
            )
    except FileNotFoundError:
        raise Exception("pyproject.toml not found")

    # Get version from codecarbon/_version.py
    versions["codecarbon_version"] = get_version_from_file(
        "codecarbon/_version.py", r'^__version__\s*=\s*["\']([^"\']+)["\']'
    )

    # Get version from docs/edit/conf.py
    versions["docs_conf"] = get_version_from_file(
        "docs/edit/conf.py", r'^release\s*=\s*["\']([^"\']+)["\']'
    )

    return versions


def check_version_coherence(quiet=False) -> bool:
    """
    Check that all version files have the same version.

    :return: True if all versions match, False otherwise
    """
    try:
        versions = get_all_versions()

        # Get unique versions
        unique_versions = set(versions.values())

        if len(unique_versions) == 1:
            version = list(unique_versions)[0]
            if not quiet:
                logging.info(
                    f"✓ Version coherence check passed. All files have version: {version}"
                )
            return True
        else:
            logging.error(
                "✗ Version coherence check failed! Versions are inconsistent:"
            )
            for file_key, version in versions.items():
                file_mapping = {
                    "pyproject_toml": "pyproject.toml [tool.bumpver] current_version",
                    "codecarbon_version": "codecarbon/_version.py __version__",
                    "docs_conf": "docs/edit/conf.py release",
                }
                logging.error(f"  {file_mapping[file_key]}: {version}")
            logging.error(
                "\nPlease use 'bumpver' to update versions consistently across all files."
            )
            return False

    except Exception as e:
        logging.error(f"✗ Error checking version coherence: {e}")
        return False


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


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Read package version and check version coherence"
    )
    parser.add_argument(
        "-o",
        "--only_package_version",
        action="store_true",
        help="Only display current package version",
    )
    parser.add_argument(
        "-c",
        "--check_coherence",
        action="store_true",
        help="Check version coherence across all bumpver-managed files",
    )

    # Parse arguments - all arguments are optional, so this works fine with no args
    args = parser.parse_args()

    # Check version coherence first if requested
    if args.check_coherence:
        coherence_ok = check_version_coherence()
        sys.exit(0 if coherence_ok else 1)

    # If only_package_version is requested, just print version and exit
    if args.only_package_version:
        try:
            info = get_versions()
            print(f'{info["package_version"]}')
            sys.exit(0)
        except Exception as e:
            logging.error(f"Error getting version: {e}")
            sys.exit(1)

    # Default behavior: check coherence quietly, then show versions
    try:
        if not check_version_coherence(quiet=True):
            logging.error("Aborting due to version coherence issues.")
            sys.exit(1)

        info = get_versions()
        logging.info("Versions:")
        print(info)  # noqa: T201
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
