from __future__ import annotations

from pathlib import Path

import pytest
from conftest import run_git

import notebook_classifier.manifest as manifest_module
from notebook_classifier.manifest import (
    ManifestConflictError,
    ManifestValidationError,
    load_manifest_snapshot,
    prepare_manifest_change,
    write_manifest_atomic,
)


def write_commented_manifest(repository: Path) -> Path:
    path = repository / "validation" / "manifest.toml"
    path.parent.mkdir()
    path.write_text(
        """
# This ownership note must survive edits.
schema_version = 1
repository_id = "example-training"

[defaults] # repository-wide decisions
role = "unknown"
lifecycle = "active"

[[rules]]
id = "tutorials"
include = ["notebooks/*.ipynb"]

[rules.properties]
environment = "default"

[[notebooks]]
id = "tutorial"
path = "notebooks/tutorial.ipynb"

[notebooks.properties]
validation_tier = "required"
""".lstrip(),
        encoding="utf-8",
    )
    return path


def prepare_role_change(repository: Path):
    path = write_commented_manifest(repository)
    snapshot = load_manifest_snapshot(repository)
    snapshot.document["defaults"]["role"] = "tutorial"
    return path, snapshot, prepare_manifest_change(snapshot, snapshot.document)


def test_round_trip_preserves_comments_and_writes_reviewed_diff(
    course_repository: Path,
) -> None:
    path, _, change = prepare_role_change(course_repository)

    assert "# This ownership note must survive edits." in change.candidate_text
    assert "[defaults] # repository-wide decisions" in change.candidate_text
    assert '-role = "unknown"' in change.diff
    assert '+role = "tutorial"' in change.diff

    write_manifest_atomic(change)

    written = path.read_text(encoding="utf-8")
    assert written == change.candidate_text
    assert "# This ownership note must survive edits." in written


def test_no_op_round_trip_is_byte_identical(course_repository: Path) -> None:
    path = write_commented_manifest(course_repository)
    snapshot = load_manifest_snapshot(course_repository)

    change = prepare_manifest_change(snapshot, snapshot.document)

    assert change.candidate_text == path.read_text(encoding="utf-8")
    assert change.diff == ""


def test_new_manifest_can_be_created_atomically(course_repository: Path) -> None:
    snapshot = load_manifest_snapshot(course_repository, allow_missing=True)
    snapshot.document["schema_version"] = 1
    snapshot.document["repository_id"] = "example-training"

    change = prepare_manifest_change(snapshot, snapshot.document)
    write_manifest_atomic(change)

    assert snapshot.path.read_text(encoding="utf-8") == change.candidate_text


def test_manifest_source_change_blocks_write(course_repository: Path) -> None:
    path, _, change = prepare_role_change(course_repository)
    original = path.read_text(encoding="utf-8")
    concurrent = original + "\n# Concurrent maintainer edit.\n"
    path.write_text(concurrent, encoding="utf-8")

    with pytest.raises(ManifestConflictError, match="manifest changed"):
        write_manifest_atomic(change)

    assert path.read_text(encoding="utf-8") == concurrent


def test_repository_commit_change_blocks_write(course_repository: Path) -> None:
    path, _, change = prepare_role_change(course_repository)
    original = path.read_text(encoding="utf-8")
    marker = course_repository / "changed-after-review.txt"
    marker.write_text("changed\n", encoding="utf-8")
    run_git(course_repository, "add", marker.name)
    run_git(
        course_repository,
        "-c",
        "user.name=Notebook Classifier Tests",
        "-c",
        "user.email=notebook-classifier@example.invalid",
        "commit",
        "-m",
        "Change repository after review",
    )

    with pytest.raises(ManifestConflictError, match="repository commit changed"):
        write_manifest_atomic(change)

    assert path.read_text(encoding="utf-8") == original


def test_notebook_change_without_commit_blocks_write(course_repository: Path) -> None:
    path, _, change = prepare_role_change(course_repository)
    original = path.read_text(encoding="utf-8")
    notebook = course_repository / "notebooks" / "tutorial.ipynb"
    notebook.write_text(notebook.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(ManifestConflictError, match="notebook state changed"):
        write_manifest_atomic(change)

    assert path.read_text(encoding="utf-8") == original


def test_invalid_candidate_is_rejected_before_diff(course_repository: Path) -> None:
    write_commented_manifest(course_repository)
    snapshot = load_manifest_snapshot(course_repository)
    snapshot.document["defaults"]["not_a_property"] = "value"

    with pytest.raises(ManifestValidationError) as error:
        prepare_manifest_change(snapshot, snapshot.document)

    assert any(item.code == "schema_violation" for item in error.value.diagnostics)


def test_replace_failure_leaves_original_manifest(
    course_repository: Path,
    monkeypatch,
) -> None:
    path, _, change = prepare_role_change(course_repository)
    original = path.read_text(encoding="utf-8")

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError(f"simulated replace failure: {source} -> {destination}")

    monkeypatch.setattr(manifest_module.os, "replace", fail_replace)

    with pytest.raises(OSError, match="simulated replace failure"):
        write_manifest_atomic(change)

    assert path.read_text(encoding="utf-8") == original
    assert not list(path.parent.glob(f".{path.name}.*.tmp"))
