"""
Check that Python code blocks in docs are runnable.

Blocks whose first line is '# skip' are intentionally excluded
(e.g. examples requiring external services or heavy dependencies).

Run with: pytest scripts/check-docs-drift.py -v
"""

import pathlib

import pytest
from mktestdocs import grab_code_blocks
from mktestdocs.__main__ import exec_python


@pytest.mark.parametrize("fpath", pathlib.Path("docs").glob("**/*.md"), ids=str)
def test_doc_file(fpath):
    text = fpath.read_text()
    for block in grab_code_blocks(text, lang="python"):
        if not block.lstrip().startswith("# skip"):
            exec_python(block)
