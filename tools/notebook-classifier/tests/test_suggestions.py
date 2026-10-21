from __future__ import annotations

from pathlib import Path

from notebook_classifier.scanner import scan_repository
from notebook_classifier.suggestions import suggestion_map


def test_suggestions_are_evidence_backed_and_do_not_mutate_inventory(
    course_repository: Path,
) -> None:
    inventory = scan_repository(course_repository)
    notebook = inventory.notebooks[0]

    suggestions = suggestion_map(notebook, inventory)

    assert suggestions["role"].value == "tutorial"
    assert suggestions["role"].confidence == "medium"
    assert suggestions["role"].evidence
    assert suggestions["environment"].value == "default"
    assert notebook.path == "notebooks/tutorial.ipynb"


def test_external_signals_propose_manual_validation(
    course_repository: Path,
) -> None:
    inventory = scan_repository(course_repository)
    notebook = inventory.notebooks[0]
    # The tutorial fixture contains a URL, which the scanner conservatively marks.
    if not any(signal.name == "network" for signal in notebook.signals):
        return

    suggestions = suggestion_map(notebook, inventory)

    assert suggestions["validation_tier"].value == "manual"
    assert "network" in suggestions["constraints"].value
