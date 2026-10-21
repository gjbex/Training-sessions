"""Persist resumable manifest drafts outside course worktrees."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import tomlkit
from tomlkit.exceptions import ParseError
from tomlkit.toml_document import TOMLDocument

from notebook_classifier.manifest import ManifestChange

DRAFT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Draft:
    """A loaded draft tied to one repository revision and manifest source."""

    path: Path
    repository_root: Path
    starting_commit: str
    repository_notebook_digest: str
    manifest_relative_path: str
    manifest_source_digest: str | None
    candidate_digest: str
    candidate_text: str
    saved_at: str
    document: TOMLDocument


class DraftError(RuntimeError):
    """Raised when persisted draft data is corrupt or inconsistent."""


class DraftStore:
    """XDG-compatible storage for uncommitted review state."""

    def __init__(self, root: Path | None = None):
        self.root = (root or default_state_root()).expanduser().resolve()

    def path_for(
        self,
        repository_root: Path,
        starting_commit: str,
        manifest_relative_path: str,
    ) -> Path:
        repository_key = _short_digest(str(repository_root.resolve()), length=20)
        manifest_key = _short_digest(manifest_relative_path, length=12)
        return self.root / repository_key / f"{starting_commit}-{manifest_key}.json"

    def save(
        self,
        change: ManifestChange,
        *,
        now: datetime | None = None,
    ) -> Path:
        """Atomically save the candidate associated with a reviewed change."""

        repository_root = change.repository_root.resolve()
        if self.root == repository_root or repository_root in self.root.parents:
            raise DraftError("draft storage must be outside the course repository")
        candidate_digest = _digest(change.candidate_text)
        if candidate_digest != change.candidate_digest:
            raise DraftError("candidate content does not match its recorded digest")
        saved_at = (now or datetime.now(UTC)).astimezone(UTC).isoformat()
        payload: dict[str, Any] = {
            "schema_version": DRAFT_SCHEMA_VERSION,
            "repository_root": str(repository_root),
            "starting_commit": change.expected_repository_commit,
            "repository_notebook_digest": change.expected_repository_notebook_digest,
            "manifest_relative_path": change.relative_path,
            "manifest_source_digest": change.expected_source_digest,
            "candidate_digest": change.candidate_digest,
            "candidate_text": change.candidate_text,
            "saved_at": saved_at,
        }
        destination = self.path_for(
            change.repository_root,
            change.expected_repository_commit,
            change.relative_path,
        )
        _write_json_atomic(destination, payload)
        return destination

    def load(
        self,
        repository_root: Path,
        starting_commit: str,
        manifest_relative_path: str,
    ) -> Draft | None:
        """Load a matching draft and reject corrupt or mis-keyed state."""

        resolved_root = repository_root.resolve()
        path = self.path_for(
            resolved_root,
            starting_commit,
            manifest_relative_path,
        )
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise DraftError(f"unable to read draft {path}: {error}") from error
        _validate_payload(
            payload,
            repository_root=resolved_root,
            starting_commit=starting_commit,
            manifest_relative_path=manifest_relative_path,
        )
        candidate_text = payload["candidate_text"]
        if _digest(candidate_text) != payload["candidate_digest"]:
            raise DraftError("draft candidate digest does not match its content")
        try:
            document = tomlkit.parse(candidate_text)
        except ParseError as error:
            raise DraftError(f"draft contains invalid TOML: {error}") from error
        return Draft(
            path=path,
            repository_root=resolved_root,
            starting_commit=starting_commit,
            repository_notebook_digest=payload["repository_notebook_digest"],
            manifest_relative_path=manifest_relative_path,
            manifest_source_digest=payload["manifest_source_digest"],
            candidate_digest=payload["candidate_digest"],
            candidate_text=candidate_text,
            saved_at=payload["saved_at"],
            document=document,
        )

    def delete(
        self,
        repository_root: Path,
        starting_commit: str,
        manifest_relative_path: str,
    ) -> bool:
        """Delete one draft after a successful save or explicit discard."""

        path = self.path_for(
            repository_root,
            starting_commit,
            manifest_relative_path,
        )
        if not path.exists():
            return False
        path.unlink()
        return True


def default_state_root() -> Path:
    """Return the Linux XDG state directory for this application."""

    configured = os.environ.get("XDG_STATE_HOME")
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_absolute():
            return candidate / "notebook-classifier"
    return Path.home() / ".local" / "state" / "notebook-classifier"


def _validate_payload(
    payload: Any,
    *,
    repository_root: Path,
    starting_commit: str,
    manifest_relative_path: str,
) -> None:
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise DraftError("unsupported or missing draft schema version")
    required_strings = (
        "repository_root",
        "starting_commit",
        "repository_notebook_digest",
        "manifest_relative_path",
        "candidate_digest",
        "candidate_text",
        "saved_at",
    )
    if any(not isinstance(payload.get(key), str) for key in required_strings):
        raise DraftError("draft is missing required string fields")
    source_digest = payload.get("manifest_source_digest")
    if source_digest is not None and not isinstance(source_digest, str):
        raise DraftError("draft manifest source digest is invalid")
    if payload["repository_root"] != str(repository_root):
        raise DraftError("draft repository identity does not match")
    if payload["starting_commit"] != starting_commit:
        raise DraftError("draft starting commit does not match")
    if payload["manifest_relative_path"] != manifest_relative_path:
        raise DraftError("draft manifest path does not match")


def _write_json_atomic(destination: Path, payload: dict[str, Any]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
        _fsync_directory(destination.parent)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _short_digest(value: str, *, length: int) -> str:
    return _digest(value)[:length]


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
