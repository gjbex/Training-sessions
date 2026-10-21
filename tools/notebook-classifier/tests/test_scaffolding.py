from __future__ import annotations

import importlib.util
import json
import tomllib
from pathlib import Path

import pytest

from notebook_classifier.cli import main
from notebook_classifier.manifest import resolve_manifest
from notebook_classifier.planning import create_validation_plan
from notebook_classifier.scaffolding import (
    ScaffoldError,
    check_scaffold,
    render_scaffold,
    write_scaffold,
)
from notebook_classifier.scanner import scan_repository


def _plan(course_repository: Path) -> dict:
    manifest = course_repository / "validation" / "manifest.toml"
    manifest.parent.mkdir(exist_ok=True)
    manifest.write_text(
        """
schema_version = 1
repository_id = "example-training"

[[notebooks]]
id = "tutorial"
path = "notebooks/tutorial.ipynb"

[notebooks.properties]
role = "tutorial"
delivery_scope = "core"
output_policy = "preserve_source"
validation_tier = "required"
environment = "default"
lifecycle = "active"
constraints = []
runtime = "short"
""".lstrip(),
        encoding="utf-8",
    )
    return create_validation_plan(
        scan_repository(course_repository), resolve_manifest(course_repository)
    ).to_dict()


def _load_generated_runner(path: Path):
    spec = importlib.util.spec_from_file_location("generated_validation_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scaffold_is_disabled_manual_only_and_contains_no_false_assertion(
    course_repository: Path,
) -> None:
    rendered = render_scaffold(_plan(course_repository))
    configuration = tomllib.loads(rendered["execution.toml"])
    workflow = rendered["ci/github-actions-notebook-validation.yml"]

    assert configuration["scaffold"]["template_version"] == 1
    assert configuration["runner"]["enabled"] is False
    assert configuration["notebooks"][0]["mode"] == "not_run"
    assert "workflow_dispatch:" in workflow
    assert "  schedule:" not in workflow
    assert "pull_request:" not in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "pixi run notebook-validation-contract" in workflow
    assert not any(
        path.endswith(".py") for path in rendered if path.startswith("assertions/")
    )
    assert str(course_repository) not in "\n".join(rendered.values())
    compile(rendered["run_validation.py"], "run_validation.py", "exec")


def test_monthly_schedule_is_only_rendered_when_explicit(
    course_repository: Path,
) -> None:
    rendered = render_scaffold(_plan(course_repository), schedule="monthly")

    assert "  schedule:" in rendered["ci/github-actions-notebook-validation.yml"]


def test_scaffold_never_overwrites_and_check_is_read_only(
    course_repository: Path, tmp_path: Path
) -> None:
    rendered = render_scaffold(_plan(course_repository))
    destination = tmp_path / "review-tree"
    write_scaffold(course_repository, destination, rendered)
    original = (destination / "README.md").read_text(encoding="utf-8")

    assert check_scaffold(course_repository, destination, rendered) == ()
    with pytest.raises(ScaffoldError, match="already exists"):
        write_scaffold(course_repository, destination, rendered)

    (destination / "README.md").write_text("local adaptation\n", encoding="utf-8")
    differences = check_scaffold(course_repository, destination, rendered)

    assert differences[0].path == "README.md"
    assert differences[0].state == "changed"
    assert (destination / "README.md").read_text(encoding="utf-8") == (
        "local adaptation\n"
    )
    assert original != "local adaptation\n"


def test_scaffold_output_inside_target_repository_is_rejected(
    course_repository: Path,
) -> None:
    rendered = render_scaffold(_plan(course_repository))

    with pytest.raises(ScaffoldError, match="outside the target repository"):
        write_scaffold(
            course_repository, course_repository / "validation-scaffold", rendered
        )


def test_scaffold_check_does_not_follow_a_generated_path_outside_root(
    course_repository: Path, tmp_path: Path
) -> None:
    rendered = render_scaffold(_plan(course_repository))
    destination = tmp_path / "review-tree"
    write_scaffold(course_repository, destination, rendered)
    outside = tmp_path / "outside.md"
    outside.write_text("not scaffold content\n", encoding="utf-8")
    (destination / "README.md").unlink()
    (destination / "README.md").symlink_to(outside)

    differences = check_scaffold(course_repository, destination, rendered)

    assert ("README.md", "unsafe") in {
        (difference.path, difference.state) for difference in differences
    }


def test_generated_runner_uses_isolated_copy_and_disabled_run_is_not_run(
    course_repository: Path, tmp_path: Path
) -> None:
    plan = _plan(course_repository)
    rendered = render_scaffold(plan)
    destination = tmp_path / "review-tree"
    write_scaffold(course_repository, destination, rendered)
    runner = _load_generated_runner(destination / "run_validation.py")

    with runner.temporary_repository_copy(course_repository) as copied:
        assert copied != course_repository
        assert (copied / "notebooks/tutorial.ipynb").is_file()
        (copied / "temporary-marker").write_text("isolated", encoding="utf-8")
    assert not (course_repository / "temporary-marker").exists()

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    artifacts = tmp_path / "artifacts"
    results = tmp_path / "results.json"
    status = runner.main(
        [
            "--repository",
            str(course_repository),
            "--plan",
            str(plan_path),
            "--configuration",
            str(destination / "execution.toml"),
            "--artifact-root",
            str(artifacts),
            "--results",
            str(results),
        ]
    )
    payload = json.loads(results.read_text(encoding="utf-8"))

    assert status == 1
    assert payload["entries"][0]["outcome"] == "not_run"
    assert payload["entries"][0]["reason_code"] == (
        "runner_disabled_pending_maintainer_review"
    )


def test_scaffold_cli_create_and_check(
    course_repository: Path, tmp_path: Path, capsys
) -> None:
    _plan(course_repository)
    destination = tmp_path / "cli-review-tree"

    create_status = main(
        [
            "scaffold-validation",
            "--repository",
            str(course_repository),
            "--output-directory",
            str(destination),
        ]
    )
    capsys.readouterr()
    check_status = main(
        [
            "scaffold-validation",
            "--repository",
            str(course_repository),
            "--output-directory",
            str(destination),
            "--check",
        ]
    )

    assert create_status == check_status == 0
    assert "matches the current template" in capsys.readouterr().out
