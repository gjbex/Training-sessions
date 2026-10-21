"""Repository-level static inventory."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from notebook_classifier.git import GitRepository
from notebook_classifier.models import RepositoryInventory
from notebook_classifier.notebook import inspect_notebook

_ENVIRONMENT_FILES = (
    "pixi.toml",
    "pixi.lock",
    "pyproject.toml",
    "environment.yml",
    "environment.yaml",
    "requirements.txt",
    "Project.toml",
    "Manifest.toml",
)


def scan_repository(path: Path) -> RepositoryInventory:
    """Build a deterministic, read-only inventory of a Git repository."""

    repository = GitRepository.discover(path)
    tracked = repository.tracked_notebooks()
    notebooks = tuple(
        inspect_notebook(
            repository.safe_path(relative_path),
            relative_path=relative_path,
            blob_id=repository.blob_id(relative_path),
            last_changed_commit=repository.last_changed_commit(relative_path),
        )
        for relative_path in tracked
    )
    findings = tuple(
        f"notebook_parse_error:{notebook.path}"
        for notebook in notebooks
        if notebook.parse_error is not None
    )
    training_id, material_paths = _training_evidence(repository.root)
    pixi_environments, pixi_tasks = _pixi_evidence(repository.root)
    return RepositoryInventory(
        repository_name=repository.root.name,
        branch=repository.branch(),
        commit=repository.commit(),
        dirty=repository.dirty(),
        tracked_notebook_count=len(tracked),
        untracked_notebooks=repository.untracked_notebooks(),
        ignored_notebooks=repository.ignored_notebooks(),
        pixi_environments=pixi_environments,
        pixi_tasks=pixi_tasks,
        environment_files=tuple(
            name for name in _ENVIRONMENT_FILES if (repository.root / name).is_file()
        ),
        training_id=training_id,
        training_material_paths=material_paths,
        notebooks=notebooks,
        findings=findings,
    )


def _pixi_evidence(root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    path = root / "pixi.toml"
    if not path.is_file():
        return (), ()
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError, tomllib.TOMLDecodeError:
        return (), ()
    environments = document.get("environments", {})
    environment_names = (
        tuple(sorted(str(name) for name in environments))
        if isinstance(environments, dict)
        else ()
    )

    tasks: set[str] = set()
    default_tasks = document.get("tasks", {})
    if isinstance(default_tasks, dict):
        tasks.update(str(name) for name in default_tasks)
    features = document.get("feature", {})
    if isinstance(features, dict):
        for feature_name, feature in features.items():
            if not isinstance(feature, dict):
                continue
            feature_tasks = feature.get("tasks", {})
            if isinstance(feature_tasks, dict):
                tasks.update(f"{feature_name}:{name}" for name in feature_tasks)
    return environment_names, tuple(sorted(tasks))


def _training_evidence(root: Path) -> tuple[str | None, tuple[str, ...]]:
    path = root / "training.toml"
    if not path.is_file():
        return None, ()
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError, tomllib.TOMLDecodeError:
        return None, ()
    training_id = document.get("id")
    materials = document.get("materials", [])
    paths: set[str] = set()
    if isinstance(materials, list):
        for material in materials:
            if isinstance(material, dict):
                value = material.get("path")
                if isinstance(value, str) and value:
                    paths.add(value)
    return _string_or_none(training_id), tuple(sorted(paths))


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None
