"""Render a review-only starter tree for course-owned notebook validation."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined

from notebook_classifier import __version__
from notebook_classifier.git import GitRepository

SCAFFOLD_TEMPLATE_VERSION = 1
SCAFFOLD_CI_CHOICES = ("github-actions",)
SCAFFOLD_SCHEDULES = ("manual", "monthly")

_TEMPLATES = {
    "README.md": "README.md.j2",
    "execution.toml": "execution.toml.j2",
    "run_validation.py": "run_validation.py.j2",
    "assertions/README.md": "assertions-README.md.j2",
    "tests/test_validation_contract.py": "test_validation_contract.py.j2",
    "ci/github-actions-notebook-validation.yml": (
        "github-actions-notebook-validation.yml.j2"
    ),
    "integration-notes.md": "integration-notes.md.j2",
}


class ScaffoldError(RuntimeError):
    """Raised when a scaffold cannot be created without unsafe writes."""


@dataclass(frozen=True)
class ScaffoldDifference:
    """One missing or changed generated file."""

    path: str
    state: str


def scaffold_context(plan: dict[str, Any], *, ci: str, schedule: str) -> dict[str, Any]:
    """Build a deterministic, template-safe context from a validated plan."""

    if ci not in SCAFFOLD_CI_CHOICES:
        raise ScaffoldError(f"unsupported CI template: {ci}")
    if schedule not in SCAFFOLD_SCHEDULES:
        raise ScaffoldError(f"unsupported schedule: {schedule}")

    candidates = [
        {
            "notebook_id": entry["notebook_id"],
            "path": entry["path"],
            "environment": str(entry["properties"]["environment"]),
        }
        for entry in plan["entries"]
        if entry["action"] == "candidate" and entry["notebook_id"] is not None
    ]
    groups = [
        {
            "environment": group["environment"],
            "notebook_ids_json": json.dumps(group["notebook_ids"]),
        }
        for group in plan["environment_groups"]
    ]
    return {
        "generator_name": "training-notebook-classifier",
        "generator_version": __version__,
        "template_version": SCAFFOLD_TEMPLATE_VERSION,
        "plan_digest": plan["plan_digest"],
        "repository_id": plan["repository"]["id"],
        "repository_commit": plan["repository"]["commit"],
        "platform": plan["repository"]["platform"],
        "ci": ci,
        "schedule": schedule,
        "candidates": candidates,
        "environment_groups": groups,
    }


def render_scaffold(
    plan: dict[str, Any], *, ci: str = "github-actions", schedule: str = "manual"
) -> dict[str, str]:
    """Render every scaffold file in memory without touching either repository."""

    context = scaffold_context(plan, ci=ci, schedule=schedule)
    environment = Environment(
        autoescape=False,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    root = files("notebook_classifier").joinpath("scaffold")
    rendered: dict[str, str] = {}
    for destination, template_name in _TEMPLATES.items():
        source = root.joinpath(template_name).read_text(encoding="utf-8")
        rendered[destination] = environment.from_string(source).render(**context)
    return rendered


def write_scaffold(
    repository: Path,
    output_directory: Path,
    rendered: dict[str, str],
) -> None:
    """Write a new tree, rejecting target-repository and overwrite attempts."""

    repository_root = GitRepository.discover(repository).root
    destination = output_directory.expanduser().resolve()
    _require_external_destination(repository_root, destination)
    if destination.exists():
        raise ScaffoldError(f"output directory already exists: {destination}")
    if not destination.parent.is_dir():
        raise ScaffoldError(
            f"output directory parent does not exist: {destination.parent}"
        )

    destination.mkdir()
    try:
        for relative_path, content in rendered.items():
            target = destination.joinpath(*relative_path.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    except BaseException:
        shutil.rmtree(destination)
        raise


def check_scaffold(
    repository: Path,
    output_directory: Path,
    rendered: dict[str, str],
) -> tuple[ScaffoldDifference, ...]:
    """Compare generated files without modifying or rejecting local additions."""

    GitRepository.discover(repository)
    destination = output_directory.expanduser().resolve()
    if not destination.is_dir():
        raise ScaffoldError(f"scaffold directory does not exist: {destination}")

    differences: list[ScaffoldDifference] = []
    for relative_path, expected in rendered.items():
        target = destination.joinpath(*relative_path.split("/"))
        resolved_target = target.resolve()
        if (
            resolved_target != destination
            and destination not in resolved_target.parents
        ):
            differences.append(ScaffoldDifference(relative_path, "unsafe"))
        elif not target.is_file():
            differences.append(ScaffoldDifference(relative_path, "missing"))
        elif target.read_text(encoding="utf-8") != expected:
            differences.append(ScaffoldDifference(relative_path, "changed"))
    return tuple(differences)


def _require_external_destination(repository_root: Path, destination: Path) -> None:
    if destination == repository_root or repository_root in destination.parents:
        raise ScaffoldError(
            "the scaffold output must be outside the target repository; review and "
            "apply it separately"
        )
