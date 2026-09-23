import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "zensical.yml"
BUILD_SCRIPT = ROOT / "scripts" / "build_site.sh"
MAIN_REF_GUARD = "github.ref == 'refs/heads/main'"


def load_workflow() -> dict:
    return yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def test_production_deployment_is_restricted_to_main() -> None:
    workflow = load_workflow()
    build = workflow["jobs"]["build"]
    deploy = workflow["jobs"]["deploy"]

    guarded_steps = {
        step["name"]: step.get("if")
        for step in build["steps"]
        if step.get("name") in {"Setup Pages", "Upload artifact"}
    }

    assert set(guarded_steps) == {"Setup Pages", "Upload artifact"}
    assert all(MAIN_REF_GUARD in condition for condition in guarded_steps.values())
    assert MAIN_REF_GUARD in deploy["if"]


def test_ci_uses_a_fixed_python_and_runner() -> None:
    workflow = load_workflow()
    build_steps = workflow["jobs"]["build"]["steps"]
    setup_uv = next(step for step in build_steps if step.get("name") == "Set up uv")

    assert setup_uv["with"]["version"] == "0.12.5"
    assert setup_uv["with"]["python-version"] == "3.12.14"
    assert workflow["jobs"]["build"]["runs-on"] == "ubuntu-24.04"
    assert workflow["jobs"]["deploy"]["runs-on"] == "ubuntu-24.04"


def test_build_uses_the_locked_runtime_without_development_tools() -> None:
    build_script = BUILD_SCRIPT.read_text(encoding="utf-8")

    assert build_script.count("uv run --locked --no-dev") == 5
    assert "uvx" not in build_script


def test_all_site_configs_enable_pruned_navigation_and_custom_templates() -> None:
    for filename in ("zensical.toml", "zensical.ja.toml", "zensical.en.toml"):
        config = tomllib.loads((ROOT / filename).read_text(encoding="utf-8"))
        theme = config["project"]["theme"]

        assert theme["custom_dir"] == "overrides"
        assert "navigation.prune" in theme["features"]
        assert "navigation.expand" not in theme["features"]
