from __future__ import annotations

from pathlib import Path

import pytest

import notebook_classifier.preview as preview_module
from notebook_classifier.preview import build_preview

FIXTURES = Path(__file__).parent / "fixtures"


def test_preview_escapes_raw_html_and_omits_output_payloads() -> None:
    preview = build_preview(FIXTURES / "hostile.ipynb")
    rendered = "\n".join(str(cell.rendered_source) for cell in preview.cells)

    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "onerror=alert" not in rendered
    assert preview.cells[1].outputs[0].mime_types == ("text/html",)


def test_preview_does_not_execute_shell_escape(tmp_path: Path) -> None:
    notebook = tmp_path / "hostile.ipynb"
    notebook.write_bytes((FIXTURES / "hostile.ipynb").read_bytes())

    build_preview(notebook)

    assert not (tmp_path / "SHOULD_NOT_EXIST").exists()


def test_preview_refuses_notebook_above_size_limit(monkeypatch) -> None:
    monkeypatch.setattr(preview_module, "MAX_NOTEBOOK_BYTES", 1)

    with pytest.raises(ValueError, match="safe preview limit"):
        build_preview(FIXTURES / "tutorial.ipynb")
