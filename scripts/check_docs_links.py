#!/usr/bin/env python3
"""Validate href/src targets in the built documentation site.

Run after ``zensical build`` (default ``site/``). Exits with code 1 if any
checked link is invalid.

By default only **local** links (under the site directory) are validated, so
CI does not depend on live docs or third-party HTTP behavior. Pass
``--external`` to also request every ``http(s)`` URL (slower; may need tuning).

Args:
    argv: See ``--help``.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER_AGENT = "codecarbon-docs-link-check/1.0 (+https://github.com/mlco2/codecarbon)"
REQUEST_TIMEOUT = 15.0
MAX_WORKERS = 12

IGNORE_EXTERNAL_PREFIXES: tuple[str, ...] = (
    "mailto:",
    "tel:",
    "javascript:",
)

IGNORE_EXTERNAL_GLOBS: tuple[str, ...] = (
    "https://fonts.googleapis.com/*",
    "https://fonts.gstatic.com/*",
)

SKIP_LOCAL_HREFS: frozenset[str] = frozenset({".", "..", "./", "../"})


def _is_github_host(url: str) -> bool:
    """True if URL host is github.com or a subdomain (not e.g. evilgithub.com)."""
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return host == "github.com" or host.endswith(".github.com")


def _matches_glob(url: str, pattern: str) -> bool:
    from fnmatch import fnmatch

    return fnmatch(url, pattern)


def _local_href_skip_ok(raw_href: str) -> tuple[bool, str] | None:
    """Return (True, reason) if href needs no filesystem check; None to resolve path."""
    if not raw_href or raw_href.startswith("#"):
        return True, "fragment-only"
    if raw_href in SKIP_LOCAL_HREFS:
        return True, "skip-navigation-href"
    parsed = urllib.parse.urlsplit(raw_href)
    if parsed.scheme in ("http", "https", "mailto", "tel", "javascript", "data"):
        if parsed.scheme in ("http", "https"):
            return True, "external-delegated"
        return True, "skipped-scheme"
    if parsed.netloc:
        return True, "other-scheme"
    return None


def _resolved_candidate_under_site(
    site_root: Path, source_html: Path, path_part: str
) -> tuple[Path | None, str]:
    """Resolve path to absolute Path under site_root, or (None, error)."""
    if path_part.startswith("/"):
        candidate = (site_root / path_part.lstrip("/")).resolve()
    else:
        candidate = (source_html.parent / path_part).resolve()
    try:
        candidate.relative_to(site_root.resolve())
    except ValueError:
        return None, f"escapes site root: {candidate}"
    return candidate, ""


def _match_local_file(
    site_root: Path, candidate: Path, fragment: str
) -> tuple[bool, str]:
    """Return (ok, detail) after checking candidate against built site layout."""
    if candidate.is_dir():
        index_file = candidate / "index.html"
        if index_file.is_file():
            ok = _fragment_ok(index_file, fragment)
            return ok, str(index_file) + (f"#{fragment}" if fragment else "")
        if candidate.name == "how-to" and candidate == site_root / "how-to":
            return True, "skip-how-to-section-root-without-index"
        return False, f"missing index in directory {candidate}"

    if candidate.is_file():
        ok = _fragment_ok(candidate, fragment)
        return ok, str(candidate) + (f"#{fragment}" if fragment else "")

    if candidate.suffix == ".md":
        html_dir = candidate.with_suffix("")
        idx = html_dir / "index.html"
        if idx.is_file():
            return _fragment_ok(idx, fragment), str(idx)
        if html_dir.is_dir() and (html_dir / "index.html").is_file():
            idx2 = html_dir / "index.html"
            return _fragment_ok(idx2, fragment), str(idx2)

    html_path = candidate.with_suffix(".html")
    if html_path.is_file():
        return _fragment_ok(html_path, fragment), str(candidate)

    nested = candidate.parent / candidate.name / "index.html"
    if candidate.parent.is_dir() and nested.is_file():
        return _fragment_ok(nested, fragment), str(nested)

    return False, f"not found: {candidate}"


def _local_target_exists(
    site_root: Path, source_html: Path, raw_href: str
) -> tuple[bool, str]:
    """Return (ok, detail) for a same-origin path or relative URL."""
    skip = _local_href_skip_ok(raw_href)
    if skip is not None:
        return skip
    parsed = urllib.parse.urlsplit(raw_href)
    path_part = parsed.path or "."
    candidate, err = _resolved_candidate_under_site(site_root, source_html, path_part)
    if candidate is None:
        return False, err
    return _match_local_file(site_root, candidate, parsed.fragment)


def _fragment_ok(html_file: Path, fragment: str) -> bool:
    if not fragment:
        return True
    text = html_file.read_text(encoding="utf-8", errors="replace")
    if re.search(rf'\b(?:id|name)=["\']{re.escape(fragment)}["\']', text):
        return True
    slug_pat = rf'\bid=["\']{re.escape(fragment)}["\']'
    return re.search(slug_pat, text) is not None


def _check_external(session: requests.Session, url: str) -> tuple[bool, str]:
    if url.startswith("http://localhost") or url.startswith("http://127.0.0.1"):
        return True, "skip-localhost"
    for pat in IGNORE_EXTERNAL_GLOBS:
        if _matches_glob(url, pat):
            return True, "ignored-glob"
    try:
        r = session.head(url, allow_redirects=True, timeout=REQUEST_TIMEOUT)
        if r.status_code in (405, 501):
            r = session.get(
                url, allow_redirects=True, timeout=REQUEST_TIMEOUT, stream=True
            )
            r.close()
        if r.status_code == 403 and _is_github_host(url):
            return True, "skip-github-403"
        if 200 <= r.status_code < 400:
            return True, str(r.status_code)
        return False, f"HTTP {r.status_code}"
    except requests.RequestException as e:
        return False, str(e)


def collect_checks(site_root: Path) -> list[tuple[Path, str, str, str]]:
    """Rows: (source_html, attr_name, url, kind) kind is local|external."""
    rows: list[tuple[Path, str, str, str]] = []
    for html_path in sorted(site_root.rglob("*.html")):
        if "assets" in html_path.parts and "javascripts" in html_path.parts:
            continue
        soup = BeautifulSoup(
            html_path.read_text(encoding="utf-8", errors="replace"), "html.parser"
        )
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if href.startswith(IGNORE_EXTERNAL_PREFIXES):
                continue
            if (
                href.startswith("http://")
                or href.startswith("https://")
                or href.startswith("//")
            ):
                rows.append((html_path, "href", href, "external"))
            else:
                rows.append((html_path, "href", href, "local"))
        for tag in soup.find_all("img", src=True):
            src = tag["src"].strip()
            if src.startswith("data:"):
                continue
            if (
                src.startswith("http://")
                or src.startswith("https://")
                or src.startswith("//")
            ):
                rows.append((html_path, "src", src, "external"))
            else:
                rows.append((html_path, "src", src, "local"))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check links in built docs under site/."
    )
    parser.add_argument(
        "site_dir",
        nargs="?",
        default="site",
        type=Path,
        help="Built site directory (default: site)",
    )
    parser.add_argument(
        "--external",
        action="store_true",
        help="Also validate http(s) URLs (slow; optional CI / manual audit).",
    )
    args = parser.parse_args()
    site_root = args.site_dir.resolve()
    if not site_root.is_dir():
        print(f"error: site directory not found: {site_root}", file=sys.stderr)
        return 1

    rows = collect_checks(site_root)
    failures: list[str] = []

    for src_html, attr, url, kind in rows:
        if kind == "local":
            ok, detail = _local_target_exists(site_root, src_html, url)
            if not ok:
                rel = src_html.relative_to(site_root)
                failures.append(f"{rel}: {attr}={url!r} -> {detail}")

    if args.external:
        external_urls = sorted({url for _, _, url, kind in rows if kind == "external"})
        session = requests.Session()
        session.headers["User-Agent"] = USER_AGENT

        def check_one(url: str) -> tuple[str, bool, str]:
            ok, msg = _check_external(session, url)
            return url, ok, msg

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(check_one, u): u for u in external_urls}
            for fut in as_completed(futures):
                url, ok, msg = fut.result()
                if not ok:
                    failures.append(f"external: {url!r} -> {msg}")

    if failures:
        print("Documentation link check failed:", file=sys.stderr)
        for line in sorted(failures):
            print(f"  {line}", file=sys.stderr)
        return 1

    n_ext = len({u for _, _, u, k in rows if k == "external"})
    if args.external:
        ext_note = f", {n_ext} external URLs checked"
    else:
        ext_note = f", {n_ext} external URLs not checked (use --external)"
    print(f"Documentation link check passed ({len(rows)} attributes{ext_note}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
