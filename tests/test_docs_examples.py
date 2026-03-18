"""Tests for documentation code examples using mktestdocs.

This file validates that code blocks in the documentation are correct and
can be executed successfully.
"""

from pathlib import Path

import pytest
from mktestdocs import check_md_file


@pytest.mark.parametrize(
    "fpath",
    [
        "docs/tutorials/python-api.md",
        "docs/explanation/why.md",
        "docs/how-to/cloud-api.md",
    ],
    ids=lambda p: Path(p).name,
)
def test_doc_python_blocks(fpath, tmp_path, monkeypatch):
    """Test independent Python code blocks from docs.

    Each block runs in isolation (memory=False).
    CWD is changed to tmp_path to isolate any file I/O.
    """
    monkeypatch.chdir(tmp_path)
    abs_fpath = Path(__file__).parent.parent / fpath
    check_md_file(str(abs_fpath))


def test_first_tracking_tutorial(tmp_path, monkeypatch):
    """Test tutorial with sequential code blocks.

    The first-tracking.md tutorial has blocks that depend on each other:
    1. Run tracker (creates emissions.csv)
    2. Read emissions.csv with pandas
    3. Access tracker.final_emissions

    Use memory=True so blocks can share state.
    """
    monkeypatch.chdir(tmp_path)
    abs_fpath = Path(__file__).parent.parent / "docs/tutorials/first-tracking.md"
    check_md_file(str(abs_fpath), memory=True)
