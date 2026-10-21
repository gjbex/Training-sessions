"""Resolve, validate, diff, and safely write notebook manifests."""

from __future__ import annotations

import copy
import difflib
import hashlib
import json
import os
import stat
import tempfile
import tomllib
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from functools import cache
from importlib.resources import files
from pathlib import Path, PurePosixPath
from typing import Any

import tomlkit
from jsonschema import Draft202012Validator, FormatChecker
from tomlkit.exceptions import ParseError
from tomlkit.toml_document import TOMLDocument

from notebook_classifier.git import GitRepository


@dataclass(frozen=True)
class ManifestDiagnostic:
    """One structural or repository-aware manifest diagnostic."""

    level: str
    code: str
    message: str
    location: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


@dataclass(frozen=True)
class ManifestSnapshot:
    """A manifest and the repository state against which it was opened."""

    repository_root: Path
    repository_commit: str
    repository_notebook_digest: str
    path: Path
    relative_path: str
    source_text: str
    source_digest: str | None
    document: TOMLDocument


@dataclass(frozen=True)
class ResolvedNotebook:
    """Effective classification and provenance for one notebook path."""

    path: str
    notebook_id: str | None
    tracked: bool
    current_blob: str | None
    properties: dict[str, Any]
    provenance: dict[str, str]
    matched_rules: tuple[str, ...]
    review_state: str
    reviewed_blob: str | None
    reviewed_commit: str | None
    reviewed_by: str | None
    reviewed_on: str | None
    replacement_id: str | None
    rename_candidates: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ManifestResolution:
    """Repository-wide effective manifest state."""

    schema_version: int
    repository_id: str
    repository_commit: str
    manifest_path: str
    manifest_source_digest: str
    notebooks: tuple[ResolvedNotebook, ...]
    diagnostics: tuple[ManifestDiagnostic, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ManifestChange:
    """A validated candidate tied to the source state shown in its diff."""

    repository_root: Path
    manifest_path: Path
    relative_path: str
    expected_repository_commit: str
    expected_repository_notebook_digest: str
    expected_source_digest: str | None
    candidate_text: str
    candidate_digest: str
    diff: str
    diagnostics: tuple[ManifestDiagnostic, ...]


class ManifestError(RuntimeError):
    """Base class for actionable manifest-engine failures."""


class ManifestValidationError(ManifestError):
    """Raised when a candidate manifest has validation errors."""

    def __init__(self, diagnostics: tuple[ManifestDiagnostic, ...]):
        self.diagnostics = diagnostics
        codes = ", ".join(
            diagnostic.code for diagnostic in diagnostics if diagnostic.level == "error"
        )
        super().__init__(f"manifest validation failed: {codes or 'unknown error'}")


class ManifestConflictError(ManifestError):
    """Raised when repository state changed after review."""


def load_manifest_snapshot(
    repository_path: Path,
    manifest_path: Path = Path("validation/manifest.toml"),
    *,
    allow_missing: bool = False,
) -> ManifestSnapshot:
    """Load a comment-preserving manifest snapshot from inside a repository."""

    repository = GitRepository.discover(repository_path)
    resolved_manifest = _resolve_inside(repository, manifest_path)
    if not resolved_manifest.is_file():
        if not allow_missing:
            raise ManifestError(f"manifest does not exist: {resolved_manifest}")
        source_text = ""
        source_digest = None
        document = tomlkit.document()
    else:
        source_text = resolved_manifest.read_text(encoding="utf-8")
        source_digest = _digest(source_text)
        try:
            document = tomlkit.parse(source_text)
        except ParseError as error:
            raise ManifestError(f"unable to parse manifest: {error}") from error
    snapshot = ManifestSnapshot(
        repository_root=repository.root,
        repository_commit=repository.commit(),
        repository_notebook_digest=_notebook_state_digest(repository),
        path=resolved_manifest,
        relative_path=resolved_manifest.relative_to(repository.root).as_posix(),
        source_text=source_text,
        source_digest=source_digest,
        document=document,
    )
    _assert_snapshot_current(repository, snapshot)
    return snapshot


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
    return validate_document(repository, document)


def validate_document(
    repository: GitRepository,
    document: Mapping[str, Any],
) -> tuple[ManifestDiagnostic, ...]:
    """Validate already parsed manifest data."""

    plain_document = dict(document)
    diagnostics = list(_structural_diagnostics(plain_document))
    if any(diagnostic.level == "error" for diagnostic in diagnostics):
        return tuple(diagnostics)
    diagnostics.extend(_semantic_diagnostics(repository, plain_document))
    return tuple(diagnostics)


def resolve_manifest(
    repository_path: Path,
    manifest_path: Path = Path("validation/manifest.toml"),
) -> ManifestResolution:
    """Resolve defaults, ordered rules, and explicit notebook overrides."""

    snapshot = load_manifest_snapshot(repository_path, manifest_path)
    document = tomllib.loads(snapshot.source_text)
    return resolve_document(snapshot, document)


def resolve_document(
    snapshot: ManifestSnapshot,
    document: Mapping[str, Any],
) -> ManifestResolution:
    """Resolve an in-memory candidate against the snapshot's repository state."""

    repository = GitRepository.discover(snapshot.repository_root)
    _assert_snapshot_current(repository, snapshot)
    diagnostics = validate_document(repository, document)
    if any(diagnostic.level == "error" for diagnostic in diagnostics):
        raise ManifestValidationError(diagnostics)

    tracked_paths = repository.tracked_notebooks()
    tracked_set = set(tracked_paths)
    current_blobs = dict(repository.blob_ids(tracked_paths))
    paths_by_blob: dict[str, list[str]] = {}
    for path, blob in current_blobs.items():
        paths_by_blob.setdefault(blob, []).append(path)

    explicit_entries = {
        entry["path"]: entry
        for entry in document.get("notebooks", [])
        if isinstance(entry, dict)
    }
    all_paths = sorted(tracked_set | set(explicit_entries))
    resolved_notebooks: list[ResolvedNotebook] = []
    for path in all_paths:
        explicit = explicit_entries.get(path)
        properties, provenance, matched_rules = _resolve_properties(
            document, path, explicit
        )
        current_blob = current_blobs.get(path)
        reviewed_blob = _optional_string(explicit, "reviewed_blob")
        if path not in tracked_set:
            review_state = "missing"
        elif reviewed_blob is None:
            review_state = "unreviewed"
        elif reviewed_blob == current_blob:
            review_state = "current"
        else:
            review_state = "stale"

        rename_candidates = (
            tuple(sorted(paths_by_blob.get(reviewed_blob, ())))
            if review_state == "missing" and reviewed_blob is not None
            else ()
        )
        resolved_notebooks.append(
            ResolvedNotebook(
                path=path,
                notebook_id=_optional_string(explicit, "id"),
                tracked=path in tracked_set,
                current_blob=current_blob,
                properties=properties,
                provenance=provenance,
                matched_rules=matched_rules,
                review_state=review_state,
                reviewed_blob=reviewed_blob,
                reviewed_commit=_optional_string(explicit, "reviewed_commit"),
                reviewed_by=_optional_string(explicit, "reviewed_by"),
                reviewed_on=_optional_string(explicit, "reviewed_on"),
                replacement_id=_optional_string(explicit, "replacement_id"),
                rename_candidates=rename_candidates,
            )
        )

    resolution = ManifestResolution(
        schema_version=int(document["schema_version"]),
        repository_id=str(document["repository_id"]),
        repository_commit=repository.commit(),
        manifest_path=snapshot.relative_path,
        manifest_source_digest=snapshot.source_digest or _digest(""),
        notebooks=tuple(resolved_notebooks),
        diagnostics=tuple(
            diagnostic for diagnostic in diagnostics if diagnostic.level != "error"
        ),
    )
    _assert_snapshot_current(repository, snapshot)
    return resolution


def prepare_manifest_change(
    snapshot: ManifestSnapshot,
    document: TOMLDocument,
) -> ManifestChange:
    """Validate a candidate and generate the exact diff a reviewer must approve."""

    repository = GitRepository.discover(snapshot.repository_root)
    _assert_snapshot_current(repository, snapshot)
    candidate_text = tomlkit.dumps(document)
    try:
        candidate_data = tomllib.loads(candidate_text)
    except tomllib.TOMLDecodeError as error:
        raise ManifestError(f"unable to serialize manifest: {error}") from error
    diagnostics = validate_document(repository, candidate_data)
    if any(diagnostic.level == "error" for diagnostic in diagnostics):
        raise ManifestValidationError(diagnostics)

    diff = "".join(
        difflib.unified_diff(
            snapshot.source_text.splitlines(keepends=True),
            candidate_text.splitlines(keepends=True),
            fromfile=f"a/{snapshot.relative_path}",
            tofile=f"b/{snapshot.relative_path}",
        )
    )
    change = ManifestChange(
        repository_root=snapshot.repository_root,
        manifest_path=snapshot.path,
        relative_path=snapshot.relative_path,
        expected_repository_commit=snapshot.repository_commit,
        expected_repository_notebook_digest=snapshot.repository_notebook_digest,
        expected_source_digest=snapshot.source_digest,
        candidate_text=candidate_text,
        candidate_digest=_digest(candidate_text),
        diff=diff,
        diagnostics=diagnostics,
    )
    _assert_snapshot_current(repository, snapshot)
    return change


def write_manifest_atomic(change: ManifestChange) -> None:
    """Atomically write a reviewed change if repository state is unchanged."""

    repository = GitRepository.discover(change.repository_root)
    if _digest(change.candidate_text) != change.candidate_digest:
        raise ManifestConflictError("candidate content changed after diff review")
    resolved_path = _resolve_inside(repository, change.manifest_path)
    if resolved_path != change.manifest_path:
        raise ManifestConflictError("manifest destination changed after review")
    _assert_change_base(repository, change)

    candidate_data = tomllib.loads(change.candidate_text)
    diagnostics = validate_document(repository, candidate_data)
    if any(diagnostic.level == "error" for diagnostic in diagnostics):
        raise ManifestValidationError(diagnostics)

    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{resolved_path.name}.",
        suffix=".tmp",
        dir=resolved_path.parent,
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(change.candidate_text)
            handle.flush()
            os.fsync(handle.fileno())
        if resolved_path.exists():
            os.chmod(temporary_path, stat.S_IMODE(resolved_path.stat().st_mode))
        _assert_change_base(repository, change)
        os.replace(temporary_path, resolved_path)
        _fsync_directory(resolved_path.parent)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


@cache
def _schema() -> dict[str, Any]:
    resource = files("notebook_classifier.schemas").joinpath(
        "notebook-validation.schema.json"
    )
    return json.loads(resource.read_text(encoding="utf-8"))


def _vocabulary_defaults() -> dict[str, Any]:
    properties = _schema()["$defs"]["classificationProperties"]["properties"]
    return {
        name: copy.deepcopy(definition["default"])
        for name, definition in properties.items()
        if "default" in definition
    }


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

    tracked = set(repository.tracked_notebooks())
    historical_paths = {
        notebook["path"]
        for notebook in notebooks
        if isinstance(notebook, dict) and isinstance(notebook.get("path"), str)
    }
    known_paths = tracked | historical_paths
    for rule_index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            continue
        unsafe = False
        for pattern_kind in ("include", "exclude"):
            for pattern_index, pattern in enumerate(rule.get(pattern_kind, [])):
                if not _safe_relative_posix_path(pattern):
                    unsafe = True
                    diagnostics.append(
                        ManifestDiagnostic(
                            "error",
                            "unsafe_rule_pattern",
                            f"rule pattern must be repository-relative: {pattern}",
                            f"rules.{rule_index}.{pattern_kind}.{pattern_index}",
                        )
                    )
        if (
            not unsafe
            and not rule.get("retain_if_unmatched", False)
            and not any(_rule_matches(path, rule) for path in known_paths)
        ):
            diagnostics.append(
                ManifestDiagnostic(
                    "error",
                    "rule_matches_nothing",
                    "rule does not match a current or historical notebook: "
                    f"{rule['id']}",
                    f"rules.{rule_index}",
                )
            )

    notebook_ids = {
        notebook["id"] for notebook in notebooks if isinstance(notebook, dict)
    }
    replacements: dict[str, str] = {}
    for index, notebook in enumerate(notebooks):
        if not isinstance(notebook, dict):
            continue
        location = f"notebooks.{index}"
        path = notebook.get("path")
        properties, _, _ = _resolve_properties(document, str(path), notebook)
        lifecycle = properties["lifecycle"]
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
            else:
                replacements[str(notebook["id"])] = str(replacement_id)
        elif replacement_id:
            diagnostics.append(
                ManifestDiagnostic(
                    "error",
                    "replacement_unexpected",
                    "replacement_id is only valid when lifecycle is replaced",
                    f"{location}.replacement_id",
                )
            )
    diagnostics.extend(_replacement_cycle_diagnostics(replacements))

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


def _resolve_properties(
    document: Mapping[str, Any],
    path: str,
    explicit: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, str], tuple[str, ...]]:
    properties = _vocabulary_defaults()
    provenance = {name: "vocabulary_default" for name in properties}

    for name, value in document.get("defaults", {}).items():
        properties[name] = copy.deepcopy(value)
        provenance[name] = "repository_default"

    matched_rules: list[str] = []
    for rule in document.get("rules", []):
        if not isinstance(rule, Mapping) or not _rule_matches(path, rule):
            continue
        rule_id = str(rule["id"])
        matched_rules.append(rule_id)
        for name, value in rule.get("properties", {}).items():
            properties[name] = copy.deepcopy(value)
            provenance[name] = f"rule:{rule_id}"

    if explicit is not None:
        for name, value in explicit.get("properties", {}).items():
            properties[name] = copy.deepcopy(value)
            provenance[name] = "notebook_override"
    return properties, provenance, tuple(matched_rules)


def _rule_matches(path: str, rule: Mapping[str, Any]) -> bool:
    candidate = PurePosixPath(path)
    included = any(candidate.full_match(pattern) for pattern in rule.get("include", []))
    excluded = any(candidate.full_match(pattern) for pattern in rule.get("exclude", []))
    return included and not excluded


def _replacement_cycle_diagnostics(
    replacements: Mapping[str, str],
) -> tuple[ManifestDiagnostic, ...]:
    diagnostics: list[ManifestDiagnostic] = []
    emitted: set[frozenset[str]] = set()
    for start in replacements:
        order: list[str] = []
        positions: dict[str, int] = {}
        current = start
        while current in replacements:
            if current in positions:
                cycle = order[positions[current] :]
                key = frozenset(cycle)
                if key not in emitted:
                    emitted.add(key)
                    diagnostics.append(
                        ManifestDiagnostic(
                            "error",
                            "replacement_cycle",
                            "replacement cycle: " + " -> ".join([*cycle, cycle[0]]),
                        )
                    )
                break
            positions[current] = len(order)
            order.append(current)
            current = replacements[current]
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


def _optional_string(entry: Mapping[str, Any] | None, key: str) -> str | None:
    if entry is None:
        return None
    value = entry.get(key)
    return str(value) if value is not None else None


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


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _current_source_digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return _digest(path.read_text(encoding="utf-8"))


def _notebook_state_digest(repository: GitRepository) -> str:
    records: list[str] = []
    for state, paths in (
        ("tracked", repository.tracked_notebooks()),
        ("untracked", repository.untracked_notebooks()),
    ):
        for path, blob_id in repository.blob_ids(paths):
            records.append(f"{state}\0{path}\0{blob_id}\0")
    return _digest("".join(records))


def _assert_snapshot_current(
    repository: GitRepository,
    snapshot: ManifestSnapshot,
) -> None:
    if repository.commit() != snapshot.repository_commit:
        raise ManifestConflictError("repository commit changed after manifest load")
    if _notebook_state_digest(repository) != snapshot.repository_notebook_digest:
        raise ManifestConflictError("notebook state changed after manifest load")
    if _current_source_digest(snapshot.path) != snapshot.source_digest:
        raise ManifestConflictError("manifest changed after it was loaded")


def _assert_change_base(
    repository: GitRepository,
    change: ManifestChange,
) -> None:
    if repository.commit() != change.expected_repository_commit:
        raise ManifestConflictError("repository commit changed after manifest review")
    if _notebook_state_digest(repository) != change.expected_repository_notebook_digest:
        raise ManifestConflictError("notebook state changed after manifest review")
    if _current_source_digest(change.manifest_path) != change.expected_source_digest:
        raise ManifestConflictError("manifest changed after its diff was reviewed")


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
