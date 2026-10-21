from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from notebook_classifier.drafts import DraftError, DraftStore, default_state_root
from notebook_classifier.manifest import (
    load_manifest_snapshot,
    prepare_manifest_change,
)


def write_manifest(repository: Path) -> None:
    path = repository / "validation" / "manifest.toml"
    path.parent.mkdir()
    path.write_text(
        """
# Drafts must preserve this comment.
schema_version = 1
repository_id = "example-training"

[defaults]
role = "unknown"

[[notebooks]]
id = "tutorial"
path = "notebooks/tutorial.ipynb"

[notebooks.properties]
validation_tier = "required"
""".lstrip(),
        encoding="utf-8",
    )


def prepare_change(repository: Path):
    write_manifest(repository)
    snapshot = load_manifest_snapshot(repository)
    snapshot.document["defaults"]["role"] = "tutorial"
    change = prepare_manifest_change(snapshot, snapshot.document)
    return snapshot, change


def test_draft_round_trip_is_outside_repository_and_comment_preserving(
    course_repository: Path,
    tmp_path: Path,
) -> None:
    snapshot, change = prepare_change(course_repository)
    store = DraftStore(tmp_path / "state")
    saved = store.save(change, now=datetime(2026, 10, 21, 12, 0, tzinfo=UTC))

    assert not saved.is_relative_to(course_repository)
    loaded = store.load(
        course_repository,
        snapshot.repository_commit,
        snapshot.relative_path,
    )

    assert loaded is not None
    assert loaded.saved_at == "2026-10-21T12:00:00+00:00"
    assert loaded.manifest_source_digest == snapshot.source_digest
    assert loaded.candidate_text == change.candidate_text
    assert "# Drafts must preserve this comment." in loaded.candidate_text
    assert loaded.document["defaults"]["role"] == "tutorial"

    assert store.delete(
        course_repository,
        snapshot.repository_commit,
        snapshot.relative_path,
    )
    assert not saved.exists()


def test_tampered_draft_is_rejected(
    course_repository: Path,
    tmp_path: Path,
) -> None:
    snapshot, change = prepare_change(course_repository)
    store = DraftStore(tmp_path / "state")
    saved = store.save(change)
    payload = json.loads(saved.read_text(encoding="utf-8"))
    payload["candidate_text"] += "\n# Tampered after save.\n"
    saved.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(DraftError, match="digest"):
        store.load(
            course_repository,
            snapshot.repository_commit,
            snapshot.relative_path,
        )


def test_draft_store_refuses_location_inside_course_repository(
    course_repository: Path,
) -> None:
    _, change = prepare_change(course_repository)
    store = DraftStore(course_repository / ".review-state")

    with pytest.raises(DraftError, match="outside the course repository"):
        store.save(change)


def test_default_state_root_honours_absolute_xdg_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg-state"))

    assert default_state_root() == tmp_path / "xdg-state" / "notebook-classifier"


def test_relative_xdg_state_path_is_ignored(monkeypatch) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", "relative-state")

    assert default_state_root() == (
        Path.home() / ".local" / "state" / "notebook-classifier"
    )
