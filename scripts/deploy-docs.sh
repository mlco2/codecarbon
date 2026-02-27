#!/usr/bin/env bash
# Deploy docs to gh-pages with versioning.
# Merges new version into existing gh-pages content.
# Usage: deploy-docs.sh VERSION_FULL [SITE_DIR] [DEPLOY_DIR]

set -euo pipefail

VERSION_FULL="${1:?Usage: deploy-docs.sh VERSION_FULL}"
VERSION_MINOR="${VERSION_FULL%.*}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE_DIR="${2:-site}"
DEPLOY_DIR="${3:-deploy}"

cd "$REPO_ROOT"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

if [[ ! -d .git ]]; then
  git init
  REPO_URL="https://github.com/${GITHUB_REPOSITORY:-mlco2/codecarbon}.git"
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    REPO_URL="https://x-access-token:${GITHUB_TOKEN}@${REPO_URL#https://}"
  fi
  git remote add origin "$REPO_URL"
fi

git fetch origin gh-pages --depth=1 2>/dev/null || true
if git show-ref --verify --quiet refs/remotes/origin/gh-pages 2>/dev/null; then
  git checkout -B gh-pages origin/gh-pages
else
  git checkout --orphan gh-pages
  git rm -rf . 2>/dev/null || true
fi

rm -rf "$VERSION_MINOR"
cp -r "$REPO_ROOT/$SITE_DIR" "$VERSION_MINOR"

rm -rf latest
cp -r "$VERSION_MINOR" latest

VERSIONS_JSON="versions.json"
python3 << PYEOF
import json

try:
    with open('$VERSIONS_JSON') as f:
        data = json.load(f)
except FileNotFoundError:
    data = []

data = [v for v in data if v['version'] != '$VERSION_MINOR']
for v in data:
    v['aliases'] = [a for a in v.get('aliases', []) if a != 'latest']
data.insert(0, {'version': '$VERSION_MINOR', 'title': '$VERSION_FULL', 'aliases': ['latest']})

with open('$VERSIONS_JSON', 'w') as f:
    json.dump(data, f, indent=2)
PYEOF

cat > index.html << 'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="refresh" content="0; url=latest/">
  <script>window.location.replace("latest/");</script>
</head>
<body>Redirecting to <a href="latest/">latest documentation</a>...</body>
</html>
HTMLEOF

echo "docs.codecarbon.io" > CNAME

git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add -A
if git diff --staged --quiet; then
  echo "No changes to deploy"
else
  git commit -m "Deploy docs $VERSION_FULL"
  git push origin gh-pages
fi
