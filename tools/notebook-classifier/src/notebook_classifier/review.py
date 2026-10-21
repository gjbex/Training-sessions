"""Application state and manifest editing operations for browser review."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from threading import RLock
from typing import Any

import tomlkit
from tomlkit.items import AoT, Array, Table
from tomlkit.toml_document import TOMLDocument

from notebook_classifier.drafts import DraftStore
from notebook_classifier.manifest import (
    ManifestChange,
    ManifestResolution,
    ResolvedNotebook,
    load_manifest_snapshot,
    prepare_manifest_change,
    resolve_document,
    write_manifest_atomic,
)
from notebook_classifier.models import NotebookInventory
from notebook_classifier.scanner import scan_repository

VOCABULARIES: dict[str, tuple[str, ...]] = {
    "role": (
        "tutorial",
        "exercise",
        "demonstration",
        "analysis",
        "report",
        "exploration",
        "unknown",
    ),
    "delivery_scope": (
        "core",
        "optional",
        "extended",
        "historical",
        "not_delivered",
        "unknown",
    ),
    "output_policy": (
        "preserve_source",
        "strip",
        "empty_expected",
        "declared_errors",
        "unknown",
    ),
    "validation_tier": ("required", "extended", "manual", "excluded", "unknown"),
    "lifecycle": ("active", "replaced", "retired", "suspended"),
    "runtime": ("short", "medium", "long", "unknown"),
}
CONSTRAINTS = ("gui", "network", "gpu", "hpc", "large_data", "manual_interaction")
EDITABLE_PROPERTIES = (
    "role",
    "delivery_scope",
    "output_policy",
    "validation_tier",
    "environment",
    "lifecycle",
    "runtime",
    "constraints",
    "rationale",
)
REQUIRED_DECISIONS = (
    "role",
    "delivery_scope",
    "output_policy",
    "validation_tier",
    "environment",
)
_SLUG = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class Progress:
    """Current review progress over tracked notebooks."""

    total: int
    reviewed: int
    decisions_complete: int
    complete: int
    stale: int
    unresolved: int


class ReviewState:
    """Thread-safe, single-maintainer review session."""

    def __init__(
        self,
        repository_path: Path,
        manifest_path: Path = Path("validation/manifest.toml"),
        *,
        draft_root: Path | None = None,
    ):
        self.lock = RLock()
        self.manifest_path = manifest_path
        self.drafts = DraftStore(draft_root)
        self.snapshot = load_manifest_snapshot(
            repository_path, manifest_path, allow_missing=True
        )
        self.inventory = scan_repository(self.snapshot.repository_root)
        self.document = self._initial_document()
        self.resumed_draft = False
        draft = self.drafts.load(
            self.snapshot.repository_root,
            self.snapshot.repository_commit,
            self.snapshot.relative_path,
        )
        if (
            draft is not None
            and draft.repository_notebook_digest
            == self.snapshot.repository_notebook_digest
            and draft.manifest_source_digest == self.snapshot.source_digest
        ):
            self.document = draft.document
            # Validate before accepting persisted state as the active candidate.
            prepare_manifest_change(self.snapshot, self.document)
            self.resumed_draft = True
        self._refresh_derived()

    @property
    def repository_root(self) -> Path:
        return self.snapshot.repository_root

    @property
    def has_unsaved_changes(self) -> bool:
        return bool(self.change.diff)

    def notebook_inventory(self, path: str) -> NotebookInventory:
        try:
            return self._inventory_by_path[path]
        except KeyError as error:
            raise ValueError(f"unknown tracked notebook: {path}") from error

    def resolved_notebook(self, path: str) -> ResolvedNotebook:
        try:
            return self._resolved_by_path[path]
        except KeyError as error:
            raise ValueError(f"unknown notebook classification: {path}") from error

    def progress(self) -> Progress:
        tracked = [
            notebook for notebook in self.resolution.notebooks if notebook.tracked
        ]
        reviewed = sum(notebook.review_state == "current" for notebook in tracked)
        decisions_complete = sum(
            not self.missing_required_decisions(notebook) for notebook in tracked
        )
        complete = sum(self._is_complete(notebook) for notebook in tracked)
        stale = sum(notebook.review_state == "stale" for notebook in tracked)
        return Progress(
            total=len(tracked),
            reviewed=reviewed,
            decisions_complete=decisions_complete,
            complete=complete,
            stale=stale,
            unresolved=len(tracked) - complete,
        )

    def unresolved_notebooks(self) -> tuple[ResolvedNotebook, ...]:
        return tuple(
            notebook
            for notebook in self.resolution.notebooks
            if notebook.tracked and not self._is_complete(notebook)
        )

    @staticmethod
    def missing_required_decisions(
        notebook: ResolvedNotebook,
    ) -> tuple[str, ...]:
        """Return required classification fields that still lack a decision."""

        return tuple(
            name
            for name in REQUIRED_DECISIONS
            if notebook.properties.get(name) in (None, "unknown", "")
        )

    def update_notebook(
        self,
        path: str,
        values: dict[str, Any],
        *,
        reviewer: str,
    ) -> None:
        """Set explicit values, or remove them when represented by ``None``."""

        reviewer = reviewer.strip()
        if not reviewer:
            raise ValueError("reviewer name is required")
        self.notebook_inventory(path)

        def mutate(document: TOMLDocument) -> None:
            entry = self._ensure_notebook_entry(document, path)
            properties = entry["properties"]
            for name, value in values.items():
                if name not in EDITABLE_PROPERTIES:
                    raise ValueError(f"unsupported property: {name}")
                if value is None or value == "":
                    properties.pop(name, None)
                else:
                    properties[name] = value
            notebook = self.notebook_inventory(path)
            entry["reviewed_by"] = reviewer
            entry["reviewed_on"] = date.today().isoformat()
            entry["reviewed_commit"] = self.snapshot.repository_commit
            entry["reviewed_blob"] = notebook.blob_id

        self._mutate(mutate)

    def bulk_update(
        self,
        paths: Iterable[str],
        *,
        property_name: str,
        value: Any,
        reviewer: str,
    ) -> None:
        selected = tuple(dict.fromkeys(paths))
        if not selected:
            raise ValueError("select at least one notebook")
        if property_name not in EDITABLE_PROPERTIES:
            raise ValueError(f"unsupported property: {property_name}")
        reviewer = reviewer.strip()
        if not reviewer:
            raise ValueError("reviewer name is required")
        for path in selected:
            self.notebook_inventory(path)

        def mutate(document: TOMLDocument) -> None:
            for path in selected:
                entry = self._ensure_notebook_entry(document, path)
                entry["properties"][property_name] = value
                notebook = self.notebook_inventory(path)
                entry["reviewed_by"] = reviewer
                entry["reviewed_on"] = date.today().isoformat()
                entry["reviewed_commit"] = self.snapshot.repository_commit
                entry["reviewed_blob"] = notebook.blob_id

        self._mutate(mutate)

    def add_rule(
        self,
        *,
        rule_id: str,
        include: str,
        exclude: Iterable[str],
        property_name: str,
        value: Any,
    ) -> None:
        if property_name not in EDITABLE_PROPERTIES:
            raise ValueError(f"unsupported property: {property_name}")
        include = include.strip()
        if not include:
            raise ValueError("rule include pattern is required")

        def mutate(document: TOMLDocument) -> None:
            rules = self._array_of_tables(document, "rules")
            rule = tomlkit.table()
            rule.add("id", rule_id.strip())
            rule.add("include", [include])
            exclusions = [item.strip() for item in exclude if item.strip()]
            if exclusions:
                rule.add("exclude", exclusions)
            properties = tomlkit.table()
            properties.add(property_name, value)
            rule.add("properties", properties)
            rules.append(rule)

        self._mutate(mutate)

    def save_manifest(self) -> Path:
        """Write the currently displayed diff and start a fresh snapshot."""

        with self.lock:
            write_manifest_atomic(self.change)
            self.drafts.delete(
                self.snapshot.repository_root,
                self.snapshot.repository_commit,
                self.snapshot.relative_path,
            )
            self.snapshot = load_manifest_snapshot(
                self.snapshot.repository_root, self.manifest_path
            )
            self.document = self.snapshot.document
            self.inventory = scan_repository(self.snapshot.repository_root)
            self.resumed_draft = False
            self._refresh_derived()
            return self.snapshot.path

    def _initial_document(self) -> TOMLDocument:
        if self.snapshot.source_text:
            return self.snapshot.document
        document = tomlkit.document()
        document.add("schema_version", 1)
        repository_id = self.inventory.training_id or _identifier(
            self.inventory.repository_name
        )
        document.add("repository_id", repository_id)
        document.add("defaults", tomlkit.table())
        document.add("rules", tomlkit.aot())
        document.add("notebooks", tomlkit.aot())
        return document

    def _mutate(self, operation: Callable[[TOMLDocument], None]) -> None:
        with self.lock:
            candidate = tomlkit.parse(tomlkit.dumps(self.document))
            operation(candidate)
            change = prepare_manifest_change(self.snapshot, candidate)
            self.drafts.save(change)
            self.document = candidate
            self._refresh_derived(change=change)

    def _refresh_derived(self, *, change: ManifestChange | None = None) -> None:
        plain = tomllib.loads(tomlkit.dumps(self.document))
        self.resolution: ManifestResolution = resolve_document(self.snapshot, plain)
        self.change = change or prepare_manifest_change(self.snapshot, self.document)
        self._inventory_by_path = {
            notebook.path: notebook for notebook in self.inventory.notebooks
        }
        self._resolved_by_path = {
            notebook.path: notebook for notebook in self.resolution.notebooks
        }

    def _ensure_notebook_entry(self, document: TOMLDocument, path: str) -> Table:
        notebooks = self._array_of_tables(document, "notebooks")
        for entry in notebooks:
            if entry.get("path") == path:
                return entry
        entry = tomlkit.table()
        entry.add("id", self._unique_notebook_id(document, path))
        entry.add("path", path)
        entry.add("properties", tomlkit.table())
        notebooks.append(entry)
        return entry

    @staticmethod
    def _array_of_tables(document: TOMLDocument, name: str) -> AoT:
        value = document.get(name)
        if value is None or isinstance(value, Array) and not value:
            value = tomlkit.aot()
            document[name] = value
        if not isinstance(value, AoT):
            raise ValueError(f"manifest {name} must be an array of tables")
        return value

    def _unique_notebook_id(self, document: TOMLDocument, path: str) -> str:
        base = _identifier(str(Path(path).with_suffix(""))) or "notebook"
        existing = {
            str(entry.get("id"))
            for entry in document.get("notebooks", ())
            if entry.get("id") is not None
        }
        candidate = base
        suffix = 2
        while candidate in existing:
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

    @staticmethod
    def _is_complete(notebook: ResolvedNotebook) -> bool:
        return (
            notebook.review_state == "current"
            and not ReviewState.missing_required_decisions(notebook)
        )


def _identifier(value: str) -> str:
    return _SLUG.sub("-", value.casefold()).strip("-")
