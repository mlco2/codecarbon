"""The drift check must actually fail when docs and code disagree."""

import importlib.util
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs" / "explanation"

_spec = importlib.util.spec_from_file_location(
    "check_docs_drift", REPO / "scripts" / "check_docs_drift.py"
)
check_docs_drift = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_docs_drift)


def _docs_copy(tmp_path):
    dest = tmp_path / "explanation"
    shutil.copytree(DOCS, dest)
    return dest


def test_passes_on_real_docs():
    assert check_docs_drift.main() == 0


def test_fails_when_doc_keeps_the_old_value(tmp_path, capsys):
    docs = _docs_copy(tmp_path)
    page = docs / "methodology.md"
    page.write_text(
        page.read_text(encoding="utf-8").replace(
            "POWER_CONSTANT = 85", "POWER_CONSTANT = 42"
        ),
        encoding="utf-8",
    )

    assert check_docs_drift.main(docs) == 1
    err = capsys.readouterr().err
    assert "POWER_CONSTANT" in err
    assert "85" in err  # the code value
    assert "42" in err  # what the docs still say
    assert "methodology.md" in err  # the file to edit


def test_fails_when_equivalence_constant_drifts(tmp_path, capsys):
    docs = _docs_copy(tmp_path)
    page = docs / "equivalences.md"
    page.write_text(
        page.read_text(encoding="utf-8").replace("0.409", "0.500"), encoding="utf-8"
    )

    assert check_docs_drift.main(docs) == 1
    assert "0.409" in capsys.readouterr().err
