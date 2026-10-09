import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "zensical.yml"
BUILD_SCRIPT = ROOT / "scripts" / "build_site.sh"


def load_workflow() -> dict:
    return yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def test_publication_uses_the_official_push_triggers() -> None:
    workflow = load_workflow()
    deploy = workflow["jobs"]["deploy"]

    assert workflow["on"] == {"push": {"branches": ["master", "main"]}}
    assert "if" not in deploy
    assert "concurrency" not in workflow
    assert deploy["environment"]["name"] == "github-pages"


def test_ci_uses_the_official_runtime_and_actions() -> None:
    workflow = load_workflow()
    deploy = workflow["jobs"]["deploy"]
    steps = deploy["steps"]
    setup_python = next(
        step for step in steps if step.get("uses") == "actions/setup-python@v6"
    )

    assert setup_python["with"]["python-version"] == "3.x"
    assert deploy["runs-on"] == "ubuntu-latest"
    assert [step["uses"] for step in steps if "uses" in step] == [
        "actions/configure-pages@v6",
        "actions/checkout@v7",
        "actions/setup-python@v6",
        "actions/upload-pages-artifact@v5",
        "actions/deploy-pages@v5",
    ]
    assert (
        next(step["run"] for step in steps if "run" in step) == "pip install zensical"
    )


def test_ci_builds_all_languages_without_running_manual_checks() -> None:
    workflow = load_workflow()
    steps = workflow["jobs"]["deploy"]["steps"]
    commands = "\n".join(step.get("run", "") for step in steps)

    for config in ("zensical.ja.toml", "zensical.toml", "zensical.en.toml"):
        assert f"zensical build --config-file {config} --clean" in commands
    for manual_command in (
        "build_site.sh",
        "check_i18n.py",
        "check_site.py",
        "generate_indexes.py",
        "pytest",
        "ruff",
        "pip-audit",
        "--strict",
        "uv ",
        "--locked",
    ):
        assert manual_command not in commands
    assert all("cache" not in step.get("with", {}) for step in steps)


def test_build_uses_the_locked_runtime_without_development_tools() -> None:
    build_script = BUILD_SCRIPT.read_text(encoding="utf-8")

    assert build_script.count("uv run --locked --no-dev") == 6
    assert "uvx" not in build_script


def test_all_site_configs_enable_pruned_navigation_and_custom_templates() -> None:
    for filename in ("zensical.toml", "zensical.ja.toml", "zensical.en.toml"):
        config = tomllib.loads((ROOT / filename).read_text(encoding="utf-8"))
        theme = config["project"]["theme"]

        assert theme["custom_dir"] == "overrides"
        assert "navigation.prune" in theme["features"]
        assert "navigation.expand" not in theme["features"]


def nav_paths(entries: list) -> list[str]:
    paths = []
    for entry in entries:
        if isinstance(entry, str):
            paths.append(entry)
        else:
            for value in entry.values():
                paths.extend(nav_paths(value) if isinstance(value, list) else [value])
    return paths


def test_navigation_covers_every_page_once_in_each_language() -> None:
    for language, filename in (
        ("zh", "zensical.toml"),
        ("ja", "zensical.ja.toml"),
        ("en", "zensical.en.toml"),
    ):
        config = tomllib.loads((ROOT / filename).read_text(encoding="utf-8"))
        paths = nav_paths(config["project"]["nav"])
        base = ROOT / "docs" / language
        expected = {p.relative_to(base).as_posix() for p in base.rglob("*.md")}
        assert set(paths) == expected
        assert len(paths) == len(expected)
        assert not (base / "_meta").exists()
