"""Structural and semantic validation for notebook manifests."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from notebook_classifier.git import GitRepository


@dataclass(frozen=True)
class ManifestDiagnostic:
    level: str
    code: str
    message: str
    location: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "location": self.location,
        }


def validate_manifest(
    repository_path: Path,
    manifest_path: Path,
) -> tuple[ManifestDiagnostic, ...]:
    """Validate a manifest structurally and against repository evidence."""

    repository = GitRepository.discover(repository_path)
    resolved_manifest = _resolve_inside(repository, manifest_path)
    if not resolved_manifest.is_file():
        return (
            ManifestDiagnostic(
                level="error",
                code="manifest_missing",
                message=f"manifest does not exist: {resolved_manifest}",
            ),
        )

    try:
        document = tomllib.loads(resolved_manifest.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return (
            ManifestDiagnostic(
                level="error",
                code="manifest_parse_error",
                message=" ".join(str(error).split()),
            ),
        )

    diagnostics = list(_structural_diagnostics(document))
    if any(diagnostic.level == "error" for diagnostic in diagnostics):
        return tuple(diagnostics)
    diagnostics.extend(_semantic_diagnostics(repository, document))
    return tuple(diagnostics)


def _schema() -> dict[str, Any]:
    resource = files("notebook_classifier.schemas").joinpath(
        "notebook-validation.schema.json"
    )
    return json.loads(resource.read_text(encoding="utf-8"))


def _structural_diagnostics(document: dict[str, Any]) -> tuple[ManifestDiagnostic, ...]:
    diagnostics: list[ManifestDiagnostic] = []
    validator = Draft202012Validator(_schema(), format_checker=FormatChecker())
    for error in sorted(
        validator.iter_errors(document), key=lambda item: list(item.path)
    ):
        location = ".".join(str(part) for part in error.absolute_path) or None
        diagnostics.append(
            ManifestDiagnostic(
                level="error",
                code="schema_violation",
                message=error.message,
                location=location,
            )
        )
    return tuple(diagnostics)


def _semantic_diagnostics(
    repository: GitRepository,
    document: dict[str, Any],
) -> tuple[ManifestDiagnostic, ...]:
    diagnostics: list[ManifestDiagnostic] = []
    notebooks = document.get("notebooks", [])
    rules = document.get("rules", [])

    diagnostics.extend(_duplicates(notebooks, "id", "duplicate_notebook_id"))
    diagnostics.extend(_duplicates(notebooks, "path", "duplicate_notebook_path"))
    diagnostics.extend(_duplicates(rules, "id", "duplicate_rule_id"))

    for rule_index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            continue
        for pattern_kind in ("include", "exclude"):
            for pattern_index, pattern in enumerate(rule.get(pattern_kind, [])):
                if not _safe_relative_posix_path(pattern):
                    diagnostics.append(
                        ManifestDiagnostic(
                            "error",
                            "unsafe_rule_pattern",
                            f"rule pattern must be repository-relative: {pattern}",
                            f"rules.{rule_index}.{pattern_kind}.{pattern_index}",
                        )
                    )

    notebook_ids = {
        notebook["id"] for notebook in notebooks if isinstance(notebook, dict)
    }
    tracked = set(repository.tracked_notebooks())
    for index, notebook in enumerate(notebooks):
        if not isinstance(notebook, dict):
            continue
        location = f"notebooks.{index}"
        path = notebook.get("path")
        properties = notebook.get("properties", {})
        lifecycle = properties.get("lifecycle", "active")
        replacement_id = notebook.get("replacement_id")
        if isinstance(path, str) and not _safe_relative_posix_path(path):
            diagnostics.append(
                ManifestDiagnostic(
                    "error",
                    "unsafe_notebook_path",
                    f"notebook path must be repository-relative: {path}",
                    f"{location}.path",
                )
            )
        elif isinstance(path, str) and path not in tracked and lifecycle == "active":
            diagnostics.append(
                ManifestDiagnostic(
                    "warning",
                    "active_notebook_not_tracked",
                    f"active notebook is not tracked by Git: {path}",
                    f"{location}.path",
                )
            )
        if lifecycle == "replaced":
            if not replacement_id:
                diagnostics.append(
                    ManifestDiagnostic(
                        "error",
                        "replacement_missing",
                        "replaced notebook requires replacement_id",
                        location,
                    )
                )
            elif replacement_id not in notebook_ids:
                diagnostics.append(
                    ManifestDiagnostic(
                        "error",
                        "replacement_unknown",
                        f"replacement_id does not resolve: {replacement_id}",
                        f"{location}.replacement_id",
                    )
                )
        elif replacement_id:
            diagnostics.append(
                ManifestDiagnostic(
                    "error",
                    "replacement_unexpected",
                    "replacement_id is only valid when lifecycle is replaced",
                    f"{location}.replacement_id",
                )
            )

    training_path = repository.root / "training.toml"
    if training_path.is_file():
        try:
            training = tomllib.loads(training_path.read_text(encoding="utf-8"))
        except OSError, tomllib.TOMLDecodeError:
            training = {}
        training_id = training.get("id")
        repository_id = document.get("repository_id")
        if isinstance(training_id, str) and repository_id != training_id:
            diagnostics.append(
                ManifestDiagnostic(
                    "error",
                    "repository_id_mismatch",
                    f"repository_id must match training.toml id {training_id!r}",
                    "repository_id",
                )
            )

    return tuple(diagnostics)


def _duplicates(
    entries: Any,
    key: str,
    code: str,
) -> tuple[ManifestDiagnostic, ...]:
    if not isinstance(entries, list):
        return ()
    seen: dict[str, int] = {}
    diagnostics: list[ManifestDiagnostic] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or not isinstance(entry.get(key), str):
            continue
        value = entry[key]
        if value in seen:
            diagnostics.append(
                ManifestDiagnostic(
                    "error",
                    code,
                    f"duplicate {key}: {value}",
                    f"{index}.{key}",
                )
            )
        else:
            seen[value] = index
    return tuple(diagnostics)


def _safe_relative_posix_path(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        bool(value)
        and "\\" not in value
        and not path.is_absolute()
        and ".." not in path.parts
    )


def _resolve_inside(repository: GitRepository, value: Path) -> Path:
    candidate = value if value.is_absolute() else repository.root / value
    resolved = candidate.resolve()
    if resolved != repository.root and repository.root not in resolved.parents:
        raise ValueError(f"manifest path escapes repository root: {value}")
    return resolved
