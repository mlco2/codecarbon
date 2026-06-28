#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# Get all release hashes from git tags and write them to a file
# The first tag to include is  the v3.0.4 because it is the first
# that uses hatchling.build as the build backend.
git tag --list --sort=v:refname \
| grep -Ev '(a|b|rc|alpha|beta)' \
| sed -n '/^v3\.0\.4$/,$p' \
| while read -r tag; do
    git rev-list -n1 "$tag"
done > "${SCRIPT_DIR}/release_hashes.txt"