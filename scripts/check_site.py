#!/usr/bin/env python3
"""Validate links and fragments in the generated multilingual static site."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SITE = ROOT / "site"
IGNORED_FRAGMENTS = {"__skip"}
MAX_HTML_BYTES = 160 * 1024
MAX_NAV_LINKS = 320


@dataclass(frozen=True)
class Page:
    path: Path
    ids: frozenset[str]
    links: tuple[str, ...]
    nav_links: int
    alternates: tuple[tuple[str, str], ...]
    selectors: tuple[tuple[str, str], ...]


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.nav_links = 0
        self.alternates: list[tuple[str, str]] = []
        self.selectors: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if element_id := attributes.get("id"):
            self.ids.add(element_id)
        if tag == "a" and (name := attributes.get("name")):
            self.ids.add(name)
        href = attributes.get("href")
        if (
            tag == "link"
            and "alternate" in (attributes.get("rel") or "").split()
            and href
            and attributes.get("hreflang")
        ):
            self.alternates.append((href, attributes["hreflang"]))
        if tag != "a" or not href:
            return
        self.links.append(href)
        if attributes.get("hreflang"):
            self.selectors.append((href, attributes["hreflang"]))
        if "md-nav__link" in (attributes.get("class") or "").split():
            self.nav_links += 1


def load_pages(site: Path) -> dict[Path, Page]:
    pages = {}
    for path in sorted(site.rglob("*.html")):
        parser = SiteParser()
        parser.feed(path.read_text(encoding="utf-8"))
        pages[path.resolve()] = Page(
            path=path.resolve(),
            ids=frozenset(parser.ids),
            links=tuple(parser.links),
            nav_links=parser.nav_links,
            alternates=tuple(parser.alternates),
            selectors=tuple(parser.selectors),
        )
    return pages


def resolve_href(source: Path, href: str, site: Path) -> Path | None:
    """Resolve a local href to a generated file, or None for external links."""
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or href.startswith(("//", "mailto:")):
        return None

    path = unquote(parsed.path)
    if not path:
        return source
    if path.startswith("/"):
        target = (site / path.lstrip("/")).resolve()
    else:
        target = (source.parent / path).resolve()

    if path.endswith("/") or target.is_dir():
        target /= "index.html"
    return target


def normalized_href(href: str) -> str | None:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
        return None
    path = unquote(parsed.path)
    if not path.endswith("/"):
        path += "/"
    return path


def page_route(path: Path, site: Path) -> tuple[str, str] | None:
    relative = path.relative_to(site)
    parts = relative.parts
    if parts and parts[0] in {"ja", "en"}:
        language = parts[0]
        parts = parts[1:]
    else:
        language = "zh"
    if parts == ("404.html",):
        return None
    is_directory_url = (
        not parts or parts[-1] == "index.html" or not parts[-1].endswith(".html")
    )
    if parts and parts[-1] == "index.html":
        parts = parts[:-1]
    route = "/" + "/".join(parts)
    if is_directory_url and not route.endswith("/"):
        route += "/"
    return language, route


def alternate_problems(site: Path, pages: dict[Path, Page]) -> list[str]:
    problems = []
    expected_languages = {"zh", "ja", "en"}
    for path, page in pages.items():
        identity = page_route(path, site)
        if identity is None:
            expected = {
                ("zh", "/"),
                ("ja", "/ja/"),
                ("en", "/en/"),
            }
        else:
            _, route = identity
            expected = {
                ("zh", route),
                ("ja", "/ja" + route),
                ("en", "/en" + route),
            }
        actual_head = {
            (language, normalized_href(href) or href)
            for href, language in page.alternates
        }
        actual_selectors = {
            (language, normalized_href(href) or href)
            for href, language in page.selectors
        }
        if actual_head != expected or len(page.alternates) != len(expected):
            problems.append(
                f"{path.relative_to(site)}: incorrect head alternates "
                f"{sorted(actual_head)!r}"
            )
        if actual_selectors != expected or len(page.selectors) != len(expected):
            problems.append(
                f"{path.relative_to(site)}: incorrect language selector targets "
                f"{sorted(actual_selectors)!r}"
            )
        if {language for language, _ in actual_head} != expected_languages:
            problems.append(f"{path.relative_to(site)}: alternate languages incomplete")
    return problems


def check_site(site: Path, pages: dict[Path, Page] | None = None) -> list[str]:
    site = site.resolve()
    if not site.is_dir():
        return [f"generated site not found: {site}"]

    pages = load_pages(site) if pages is None else pages
    if not pages:
        return [f"generated site has no HTML pages: {site}"]

    problems = alternate_problems(site, pages)
    for source, page in pages.items():
        if page.path.stat().st_size > MAX_HTML_BYTES:
            problems.append(
                f"{page.path.relative_to(site)}: HTML exceeds {MAX_HTML_BYTES} bytes"
            )
        if page.nav_links > MAX_NAV_LINKS:
            problems.append(
                f"{page.path.relative_to(site)}: navigation exceeds "
                f"{MAX_NAV_LINKS} links"
            )
        for href in page.links:
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or href.startswith(("//", "mailto:")):
                continue
            target = resolve_href(source, href, site)
            if target is None:
                continue
            try:
                target.relative_to(site)
            except ValueError:
                problems.append(
                    f"{page.path.relative_to(site)}: link escapes site: {href}"
                )
                continue
            if not target.is_file():
                problems.append(
                    f"{page.path.relative_to(site)}: missing link target: {href}"
                )
                continue
            fragment = unquote(parsed.fragment)
            if (
                fragment
                and fragment not in IGNORED_FRAGMENTS
                and target.suffix == ".html"
                and fragment not in pages[target.resolve()].ids
            ):
                problems.append(
                    f"{page.path.relative_to(site)}: missing fragment: {href}"
                )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=DEFAULT_SITE)
    args = parser.parse_args(argv)
    site = args.site.resolve()
    pages = load_pages(site) if site.is_dir() else {}
    problems = check_site(site, pages)
    if problems:
        print("site check failed:", file=sys.stderr)
        print(*(f"  {problem}" for problem in problems), sep="\n", file=sys.stderr)
        return 1

    link_count = sum(len(page.links) for page in pages.values())
    print(f"site links OK ({len(pages)} pages, {link_count} link elements)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
