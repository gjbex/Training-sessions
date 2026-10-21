"""Serializable inventory models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

INVENTORY_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StoredError:
    """A stored notebook error output."""

    cell_index: int
    name: str
    value: str


@dataclass(frozen=True)
class LocatedSignal:
    """A conservative static signal and the cells that support it."""

    name: str
    cell_indices: tuple[int, ...]


@dataclass(frozen=True)
class NotebookInventory:
    """Static facts extracted from one notebook."""

    path: str
    blob_id: str
    size_bytes: int
    last_changed_commit: str | None
    parse_error: str | None = None
    validation_warnings: tuple[str, ...] = ()
    nbformat: int | None = None
    nbformat_minor: int | None = None
    kernel_name: str | None = None
    kernel_language: str | None = None
    code_cells: int = 0
    markdown_cells: int = 0
    raw_cells: int = 0
    unexecuted_code_cells: int = 0
    non_monotonic_execution_counts: bool = False
    output_count: int = 0
    output_types: tuple[str, ...] = ()
    stored_errors: tuple[StoredError, ...] = ()
    embedded_output_bytes: int = 0
    headings: tuple[str, ...] = ()
    cell_tags: tuple[str, ...] = ()
    imports: tuple[str, ...] = ()
    magics: tuple[str, ...] = ()
    shell_escapes: tuple[str, ...] = ()
    urls: tuple[str, ...] = ()
    signals: tuple[LocatedSignal, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RepositoryInventory:
    """Deterministic static inventory for one Git repository."""

    repository_name: str
    branch: str | None
    commit: str
    dirty: bool
    tracked_notebook_count: int
    untracked_notebooks: tuple[str, ...]
    ignored_notebooks: tuple[str, ...]
    pixi_environments: tuple[str, ...]
    pixi_tasks: tuple[str, ...]
    environment_files: tuple[str, ...]
    training_id: str | None
    training_material_paths: tuple[str, ...]
    notebooks: tuple[NotebookInventory, ...]
    findings: tuple[str, ...] = field(default_factory=tuple)
    schema_version: int = INVENTORY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
