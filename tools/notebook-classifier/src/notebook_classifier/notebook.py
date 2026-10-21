"""Static, non-executing Jupyter notebook inspection."""

from __future__ import annotations

import ast
import json
import re
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any

import nbformat

from notebook_classifier.models import LocatedSignal, NotebookInventory, StoredError

_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")
_URL = re.compile(r"https?://[^\s\]\[<>()\"']+")
_IMPORT_LINE = re.compile(r"^\s*(?:from\s+([A-Za-z_][\w.]*)\s+import|import\s+(.+))")

_SIGNAL_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "interactive": tuple(
        re.compile(pattern, re.IGNORECASE)
        for pattern in (
            r"\bipywidgets\b",
            r"\binteract(?:_manual)?\s*\(",
            r"%matplotlib\s+(?:widget|notebook)",
            r"\bvpython\b",
            r"\bbokeh\b",
        )
    ),
    "network": tuple(
        re.compile(pattern, re.IGNORECASE)
        for pattern in (
            r"\brequests\b",
            r"\bhttpx\b",
            r"\burllib\b",
            r"\baiohttp\b",
            r"https?://",
        )
    ),
    "gpu": tuple(
        re.compile(pattern, re.IGNORECASE)
        for pattern in (
            r"\bcupy\b",
            r"\bnumba\.cuda\b",
            r"\btorch\.cuda\b",
            r"\btensorflow\b",
            r"\bjax\b",
        )
    ),
    "hpc": tuple(
        re.compile(pattern, re.IGNORECASE)
        for pattern in (
            r"\bmpi4py\b",
            r"\bdask\.distributed\b",
            r"\bpyspark\b",
            r"\bsbatch\b",
            r"\bsrun\b",
        )
    ),
    "subprocess": (re.compile(r"\bsubprocess\b"),),
    "randomness": tuple(
        re.compile(pattern)
        for pattern in (r"\bnp\.random\b", r"\bnumpy\.random\b", r"\brandom\.")
    ),
    "explicit_seed": tuple(
        re.compile(pattern)
        for pattern in (r"\bdefault_rng\s*\(", r"\bseed\s*\(", r"\brandom_state\s*=")
    ),
}


def inspect_notebook(
    path: Path,
    *,
    relative_path: str,
    blob_id: str,
    last_changed_commit: str | None,
) -> NotebookInventory:
    """Inspect one notebook without importing or executing its contents."""

    raw = path.read_bytes()
    base = {
        "path": relative_path,
        "blob_id": blob_id,
        "size_bytes": len(raw),
        "last_changed_commit": last_changed_commit,
    }
    try:
        text = raw.decode("utf-8")
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            notebook = nbformat.reads(text, as_version=nbformat.NO_CONVERT)
            nbformat.validate(notebook)
    except (UnicodeDecodeError, ValueError, nbformat.ValidationError) as error:
        return NotebookInventory(parse_error=_brief_error(error), **base)
    validation_warnings = tuple(
        sorted(
            {
                f"{warning.category.__name__}: {_brief_error(warning.message)}"
                for warning in caught_warnings
            }
        )
    )

    code_cells = 0
    markdown_cells = 0
    raw_cells = 0
    unexecuted = 0
    execution_counts: list[int] = []
    output_count = 0
    output_types: set[str] = set()
    stored_errors: list[StoredError] = []
    embedded_output_bytes = 0
    headings: list[str] = []
    cell_tags: set[str] = set()
    imports: set[str] = set()
    magics: set[str] = set()
    shell_escapes: set[str] = set()
    urls: set[str] = set()
    signal_cells: dict[str, set[int]] = defaultdict(set)

    for cell_index, cell in enumerate(notebook.cells):
        cell_type = cell.get("cell_type")
        source = str(cell.get("source", ""))
        urls.update(_URL.findall(source))
        metadata = cell.get("metadata", {})
        if isinstance(metadata, dict):
            tags = metadata.get("tags", [])
            if isinstance(tags, list):
                cell_tags.update(str(tag) for tag in tags if str(tag).strip())

        if cell_type == "markdown":
            markdown_cells += 1
            for line in source.splitlines():
                match = _HEADING.match(line)
                if match:
                    headings.append(match.group(1).strip())
            _record_signals(source, cell_index, signal_cells)
            continue
        if cell_type == "raw":
            raw_cells += 1
            continue
        if cell_type != "code":
            continue

        code_cells += 1
        execution_count = cell.get("execution_count")
        if execution_count is None:
            unexecuted += 1
        elif isinstance(execution_count, int):
            execution_counts.append(execution_count)

        for line in source.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("%"):
                magics.add(stripped.split(maxsplit=1)[0])
            elif stripped.startswith("!"):
                shell_escapes.add(stripped[:160])

        imports.update(_extract_imports(source))
        _record_signals(source, cell_index, signal_cells)

        for output in cell.get("outputs", []):
            output_count += 1
            output_type = str(output.get("output_type", "unknown"))
            output_types.add(output_type)
            if output_type == "error":
                stored_errors.append(
                    StoredError(
                        cell_index=cell_index,
                        name=str(output.get("ename", "")),
                        value=str(output.get("evalue", "")),
                    )
                )
            data = output.get("data", {})
            if isinstance(data, dict):
                embedded_output_bytes += sum(
                    _encoded_size(value)
                    for mime, value in data.items()
                    if mime.startswith("image/")
                    or mime in {"text/html", "application/json"}
                )

    metadata = notebook.get("metadata", {})
    kernelspec = metadata.get("kernelspec", {}) if isinstance(metadata, dict) else {}
    language_info = (
        metadata.get("language_info", {}) if isinstance(metadata, dict) else {}
    )

    signals = tuple(
        LocatedSignal(name=name, cell_indices=tuple(sorted(indices)))
        for name, indices in sorted(signal_cells.items())
    )
    return NotebookInventory(
        **base,
        validation_warnings=validation_warnings,
        nbformat=int(notebook.nbformat),
        nbformat_minor=int(notebook.nbformat_minor),
        kernel_name=_optional_text(kernelspec.get("name")),
        kernel_language=_optional_text(language_info.get("name")),
        code_cells=code_cells,
        markdown_cells=markdown_cells,
        raw_cells=raw_cells,
        unexecuted_code_cells=unexecuted,
        non_monotonic_execution_counts=any(
            current <= previous
            for previous, current in zip(
                execution_counts, execution_counts[1:], strict=False
            )
        ),
        output_count=output_count,
        output_types=tuple(sorted(output_types)),
        stored_errors=tuple(stored_errors),
        embedded_output_bytes=embedded_output_bytes,
        headings=tuple(headings),
        cell_tags=tuple(sorted(cell_tags)),
        imports=tuple(sorted(imports)),
        magics=tuple(sorted(magics)),
        shell_escapes=tuple(sorted(shell_escapes)),
        urls=tuple(sorted(urls)),
        signals=signals,
    )


def _extract_imports(source: str) -> set[str]:
    imports: set[str] = set()
    try:
        # Invalid escape sequences in notebook source are evidence to report on,
        # not warnings from the classifier itself.  Python 3.14 emits these
        # during parsing even though the source is never executed.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(source)
    except SyntaxError:
        for line in source.splitlines():
            match = _IMPORT_LINE.match(line)
            if not match:
                continue
            if match.group(1):
                imports.add(match.group(1).split(".")[0])
            else:
                for part in match.group(2).split(","):
                    name = part.strip().split(" as ", maxsplit=1)[0]
                    if name:
                        imports.add(name.split(".")[0])
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports


def _record_signals(
    source: str,
    cell_index: int,
    signal_cells: dict[str, set[int]],
) -> None:
    for signal, patterns in _SIGNAL_PATTERNS.items():
        if any(pattern.search(source) for pattern in patterns):
            signal_cells[signal].add(cell_index)


def _encoded_size(value: Any) -> int:
    if isinstance(value, str):
        return len(value.encode("utf-8"))
    if isinstance(value, list):
        return sum(_encoded_size(item) for item in value)
    return len(json.dumps(value, sort_keys=True).encode("utf-8"))


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _brief_error(error: Exception) -> str:
    return " ".join(str(error).split())[:500]
