"""Bounded, non-executing notebook previews for the local review UI."""

from __future__ import annotations

import html
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import nbformat
from markdown_it import MarkdownIt
from markupsafe import Markup
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

MAX_CELLS = 120
MAX_CELL_CHARACTERS = 16_000
MAX_NOTEBOOK_CHARACTERS = 240_000
MAX_NOTEBOOK_BYTES = 32 * 1024 * 1024


@dataclass(frozen=True)
class OutputSummary:
    """Safe metadata about an omitted notebook output."""

    output_type: str
    mime_types: tuple[str, ...]
    approximate_bytes: int


@dataclass(frozen=True)
class PreviewCell:
    """One bounded cell preview."""

    index: int
    cell_type: str
    rendered_source: Markup
    source_truncated: bool
    outputs: tuple[OutputSummary, ...]


@dataclass(frozen=True)
class NotebookPreview:
    """A bounded notebook preview that contains no rendered output payloads."""

    cells: tuple[PreviewCell, ...]
    cells_omitted: int
    content_truncated: bool


_MARKDOWN = MarkdownIt("commonmark", {"html": False, "linkify": False})
_FORMATTER = HtmlFormatter(nowrap=False, cssclass="highlight")


def build_preview(path: Path) -> NotebookPreview:
    """Read a notebook as data and render only bounded, escaped source."""

    size = path.stat().st_size
    if size > MAX_NOTEBOOK_BYTES:
        raise ValueError(
            f"notebook is {size} bytes; safe preview limit is {MAX_NOTEBOOK_BYTES}"
        )
    notebook = nbformat.read(path, as_version=nbformat.NO_CONVERT)
    previews: list[PreviewCell] = []
    remaining = MAX_NOTEBOOK_CHARACTERS
    content_truncated = False
    visible_cells = notebook.cells[:MAX_CELLS]
    for index, cell in enumerate(visible_cells):
        source = str(cell.get("source", ""))
        limit = min(MAX_CELL_CHARACTERS, max(remaining, 0))
        visible_source = source[:limit]
        truncated = len(visible_source) < len(source)
        content_truncated = content_truncated or truncated
        remaining -= len(visible_source)
        cell_type = str(cell.get("cell_type", "unknown"))
        previews.append(
            PreviewCell(
                index=index,
                cell_type=cell_type,
                rendered_source=_render_source(visible_source, cell_type),
                source_truncated=truncated,
                outputs=_summarize_outputs(cell.get("outputs", ())),
            )
        )
        if remaining <= 0:
            content_truncated = True
            break
    cells_omitted = len(notebook.cells) - len(previews)
    return NotebookPreview(
        cells=tuple(previews),
        cells_omitted=max(cells_omitted, 0),
        content_truncated=content_truncated,
    )


def preview_css() -> str:
    """Return Pygments rules used by the packaged stylesheet."""

    return _FORMATTER.get_style_defs(".highlight")


def _render_source(source: str, cell_type: str) -> Markup:
    if cell_type == "markdown":
        # Raw HTML is disabled; Markdown-It escapes it before this value is marked safe.
        return Markup(_MARKDOWN.render(source))
    if cell_type == "code":
        return Markup(highlight(source, PythonLexer(), _FORMATTER))
    escaped = html.escape(source)
    return Markup(f'<pre class="raw-source">{escaped}</pre>')


def _summarize_outputs(outputs: Any) -> tuple[OutputSummary, ...]:
    summaries: list[OutputSummary] = []
    if not isinstance(outputs, list):
        return ()
    for output in outputs:
        if not isinstance(output, dict):
            continue
        data = output.get("data", {})
        mime_types = (
            tuple(sorted(str(key) for key in data)) if isinstance(data, dict) else ()
        )
        summaries.append(
            OutputSummary(
                output_type=str(output.get("output_type", "unknown")),
                mime_types=mime_types,
                approximate_bytes=_encoded_size(output),
            )
        )
    return tuple(summaries)


def _encoded_size(value: Any) -> int:
    if isinstance(value, str):
        return len(value.encode("utf-8"))
    if isinstance(value, bytes):
        return len(value)
    if isinstance(value, dict):
        return sum(
            _encoded_size(key) + _encoded_size(item) for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return sum(_encoded_size(item) for item in value)
    return len(str(value).encode("utf-8"))
