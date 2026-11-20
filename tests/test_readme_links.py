"""Guard against README indexes referencing files that no longer exist."""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
# Markdown files whose relative links must all resolve.
CHECKED_FILES = [REPO_ROOT / "examples" / "README.md"]

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


@pytest.mark.parametrize("md_file", CHECKED_FILES, ids=lambda p: str(p.name))
def test_relative_links_exist(md_file):
    if not md_file.exists():
        # The wheel-validation job runs the tests without the rest of the repository.
        pytest.skip(f"{md_file} is not present in this checkout")
    missing = [
        target
        for target in LINK_RE.findall(md_file.read_text())
        if not target.startswith(("http://", "https://", "mailto:", "#"))
        and not (md_file.parent / target.split("#")[0]).exists()
    ]
    assert not missing, f"{md_file} links to missing paths: {missing}"
