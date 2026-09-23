from pathlib import Path

from scripts.check_site import check_site, load_pages, resolve_href


def write_page(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def language_links(route: str) -> str:
    targets = {"zh": route, "ja": "/ja" + route, "en": "/en" + route}
    head = "".join(
        f'<link rel="alternate" href="{target}" hreflang="{language}">'
        for language, target in targets.items()
    )
    selector = "".join(
        f'<a href="{target}" hreflang="{language}" class="md-select__link">'
        f"{language}</a>"
        for language, target in targets.items()
    )
    return head + selector


def make_site(tmp_path: Path) -> Path:
    site = tmp_path / "site"
    write_page(
        site / "index.html",
        f"""<!doctype html>
        <head>{language_links("/")}</head>
        <a class="md-nav__link" href="/other/">Other</a>
        <a href="#section">Current section</a>
        <a href="#__skip">Skip</a>
        <a href="https://example.test">External</a>
        <h1 id="section">Section</h1>
        """,
    )
    write_page(
        site / "other" / "index.html",
        f"<head>{language_links('/other/')}</head>"
        '<a href="../">Home</a><h1 id="target">Target</h1>',
    )
    write_page(site / "ja" / "index.html", f"<head>{language_links('/')}</head>")
    write_page(site / "en" / "index.html", f"<head>{language_links('/')}</head>")
    write_page(
        site / "ja" / "other" / "index.html",
        f"<head>{language_links('/other/')}</head>",
    )
    write_page(
        site / "en" / "other" / "index.html",
        f"<head>{language_links('/other/')}</head>",
    )
    return site


def test_generated_internal_links_and_fragments_resolve(tmp_path: Path) -> None:
    site = make_site(tmp_path)

    assert check_site(site) == []
    pages = load_pages(site.resolve())
    assert pages[(site / "index.html").resolve()].nav_links == 1


def test_missing_file_and_fragment_are_reported(tmp_path: Path) -> None:
    site = make_site(tmp_path)
    write_page(
        site / "index.html",
        '<a href="/missing/">Missing</a><a href="/other/#absent">Fragment</a>',
    )

    problems = check_site(site)

    assert any("missing link target" in problem for problem in problems)
    assert any("missing fragment" in problem for problem in problems)


def test_navigation_budget_rejects_unpruned_sidebar(tmp_path: Path) -> None:
    site = make_site(tmp_path)
    navigation = "".join(
        '<a class="md-nav__link" href="/other/">Link</a>' for _ in range(321)
    )
    write_page(
        site / "index.html",
        f"<head>{language_links('/')}</head>{navigation}",
    )

    problems = check_site(site)

    assert any("navigation exceeds" in problem for problem in problems)


def test_incorrect_page_alternates_are_reported(tmp_path: Path) -> None:
    site = make_site(tmp_path)
    write_page(
        site / "other" / "index.html",
        f"<head>{language_links('/wrong/')}</head>",
    )

    problems = check_site(site)

    assert any("incorrect head alternates" in problem for problem in problems)
    assert any("incorrect language selector targets" in problem for problem in problems)


def test_fragment_only_href_resolves_to_current_page(tmp_path: Path) -> None:
    site = make_site(tmp_path)
    source = (site / "index.html").resolve()

    assert resolve_href(source, "#section", site.resolve()) == source


def test_link_escaping_site_is_reported(tmp_path: Path) -> None:
    site = make_site(tmp_path)
    write_page(site / "index.html", '<a href="../../outside">Outside</a>')

    problems = check_site(site)

    assert any("link escapes site" in problem for problem in problems)
