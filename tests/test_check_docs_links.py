"""Tests for scripts/check_docs_links.py, the link checker run on the built docs."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_docs_links.py"

# The wheel test run only checks out tests/, without the scripts.
pytestmark = pytest.mark.skipif(
    not SCRIPT.exists(), reason="docs scripts are not part of the installed package"
)


@pytest.fixture(scope="module")
def checker():
    pytest.importorskip("bs4")
    spec = importlib.util.spec_from_file_location("check_docs_links", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _page(path: Path, *hrefs: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    links = "".join(f'<a href="{href}">x</a>' for href in hrefs)
    path.write_text(f"<html><body>{links}</body></html>", encoding="utf-8")


def _run(checker, monkeypatch, site: Path, *args: str) -> int:
    monkeypatch.setattr("sys.argv", ["check_docs_links.py", str(site), *args])
    return checker.main()


@pytest.fixture
def site(tmp_path):
    """A site built with site_url .../latest/: files at the root, links under /latest/."""
    _page(tmp_path / "index.html", "how-to/slurm/")
    _page(tmp_path / "how-to" / "slurm" / "index.html", "../../")
    _page(tmp_path / "404.html", "/latest/", "/latest/how-to/slurm/")
    return tmp_path


def test_links_under_site_url_path_resolve(checker, monkeypatch, site):
    assert _run(checker, monkeypatch, site, "--base-path", "/latest/") == 0


def test_broken_link_in_404_page_is_reported(checker, monkeypatch, site, capsys):
    _page(site / "404.html", "/latest/", "/latest/how-to/missing/")

    assert _run(checker, monkeypatch, site, "--base-path", "latest") == 1
    assert "404.html: href='/latest/how-to/missing/'" in capsys.readouterr().err


def test_absolute_link_outside_site_url_path_is_reported(
    checker, monkeypatch, site, capsys
):
    # Deployed under /latest/, "/how-to/slurm/" is a 404 even though the file exists.
    _page(site / "index.html", "/how-to/slurm/")

    assert _run(checker, monkeypatch, site, "--base-path", "/latest/") == 1
    assert "outside the site path /latest/" in capsys.readouterr().err


def test_root_base_path_keeps_absolute_links_working(checker, monkeypatch, site):
    _page(site / "404.html", "/", "/how-to/slurm/")

    assert _run(checker, monkeypatch, site, "--base-path", "/") == 0


@pytest.mark.parametrize(
    "line, expected",
    [
        ("site_url: https://docs.codecarbon.io/latest/", "/latest/"),
        ("site_url: 'https://docs.codecarbon.io/latest'", "/latest/"),
        ("site_url: https://docs.codecarbon.io/", "/"),
        ("site_name: no site_url here", "/"),
    ],
)
def test_site_url_path_reads_mkdocs_config(checker, tmp_path, line, expected):
    config = tmp_path / "mkdocs.yml"
    config.write_text(f"site_name: CodeCarbon\n{line}\n", encoding="utf-8")

    assert checker.site_url_path(config) == expected


def test_default_base_path_matches_repository_site_url(checker):
    assert checker.site_url_path() == "/latest/"


def _head_page(path: Path, head: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"<html><head>{head}</head><body></body></html>", encoding="utf-8")


def test_link_and_script_targets_are_checked(checker, monkeypatch, site, capsys):
    (site / "assets").mkdir()
    (site / "assets" / "main.css").write_text("", encoding="utf-8")
    _head_page(
        site / "404.html",
        '<link rel="stylesheet" href="/latest/assets/main.css">'
        '<link rel="icon" href="/latest/images/missing.ico">'
        '<script src="/latest/assets/missing.js"></script>',
    )

    assert _run(checker, monkeypatch, site, "--base-path", "/latest/") == 1
    err = capsys.readouterr().err
    assert "404.html: href='/latest/images/missing.ico'" in err
    assert "404.html: src='/latest/assets/missing.js'" in err
    assert "main.css" not in err


def test_preconnect_origins_and_inline_scripts_are_skipped(checker, site):
    _head_page(
        site / "index.html",
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link rel="canonical" href="https://docs.codecarbon.io/latest/">'
        "<script>var x = 1;</script>",
    )

    rows = [
        row for row in checker.collect_checks(site) if row[0] == site / "index.html"
    ]
    assert [(attr, url) for _, attr, url, _ in rows] == [
        ("href", "https://docs.codecarbon.io/latest/")
    ]
