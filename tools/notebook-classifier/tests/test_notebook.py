from __future__ import annotations

import warnings
from pathlib import Path

from notebook_classifier.notebook import _extract_imports, inspect_notebook

FIXTURES = Path(__file__).parent / "fixtures"


def inspect(name: str):
    return inspect_notebook(
        FIXTURES / name,
        relative_path=name,
        blob_id="0" * 40,
        last_changed_commit="1" * 40,
    )


def test_tutorial_inventory() -> None:
    notebook = inspect("tutorial.ipynb")

    assert notebook.parse_error is None
    assert notebook.code_cells == 1
    assert notebook.markdown_cells == 1
    assert notebook.unexecuted_code_cells == 0
    assert notebook.headings == ("Array reduction",)
    assert notebook.imports == ("numpy",)
    assert notebook.output_types == ("execute_result",)


def test_invalid_notebook_is_a_finding_not_an_exception() -> None:
    notebook = inspect("invalid.ipynb")

    assert notebook.parse_error is not None
    assert notebook.code_cells == 0


def test_notebook_validation_warnings_are_evidence_not_process_warnings() -> None:
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        notebook = inspect("exercise.ipynb")

    assert caught_warnings == []
    assert len(notebook.validation_warnings) == 1
    assert notebook.validation_warnings[0].startswith("MissingIDFieldWarning:")


def test_hostile_content_is_only_reported(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    marker = tmp_path / "SHOULD_NOT_EXIST"
    notebook = inspect("hostile.ipynb")

    assert not marker.exists()
    assert notebook.shell_escapes == ("!touch SHOULD_NOT_EXIST",)
    assert notebook.imports == ("requests", "subprocess")
    assert [signal.name for signal in notebook.signals] == ["network", "subprocess"]
    assert notebook.urls == ("https://example.invalid/data",)
    assert notebook.stored_errors[0].name == "RuntimeError"
    assert notebook.embedded_output_bytes > 0


def test_static_parsing_does_not_leak_source_warnings() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", SyntaxWarning)
        imports = _extract_imports(r"value = '\m'")

    assert imports == set()
